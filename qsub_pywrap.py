"""Submit python code to qsub systems
"""
import subprocess
from time import strftime
import os
import sys
import tempfile
from random import randint

import dill as pickle

submission_command_template = "qsub -q {queue} {extra_options} -N {job_name} {script_name}"

py_script_template = """#!{python_path}
import os
import dill as pickle

with open('{input_pickle_name}', mode='rb') as infile:
    data = pickle.load(infile)
os.remove('{input_pickle_name}')

result = data['fun'](*data['fun_args'], **data['fun_kwargs'])

with open('{output_pickle_name}', mode='wb') as outfile:
    pickle.dump(result, outfile)
"""

default_queue = 'express'

def qsubwrap(fun, *args,
             pickle_dir=None, messages_dir=None,
             queue=default_queue, extra_options='',
             verbose=False,
             **kwargs):
    """Submit a qsub job to call fun(*args, **kwargs)
        pickledir will be used to exchange input/output via pickles. Defaults to os.cwd() / qsub_pickles
        messages_dir will contain the files with stdout and stderr from the jobs. Defaults to os.cwd() / qsub_messages
        queue: name of the queue qsub will submit the job to
        extra_options will be passes directly to the qsub command.
    returns: job_name, filename of pickle which will contain result of function when the job is done
    """
    job_name = fun.__name__ + '%09d' % randint(0, 1e9)
    if verbose:
        print("Starting submission of job %s" % job_name)

    if pickle_dir is None:
        pickle_dir = os.path.join(os.getcwd(), 'qsub_pickles')
    if not os.path.exists(pickle_dir):
        os.makedirs(pickle_dir)
    if messages_dir is None:
        messages_dir = os.path.join(os.getcwd(), 'qsub_messages')
    if not os.path.exists(messages_dir):
        os.makedirs(messages_dir)
    extra_options += ' -e localhost:{messages_dir} -o localhost:{messages_dir}'.format(messages_dir=messages_dir)

    input_pickle_name = os.path.join(pickle_dir,
                                     strftime('input_%Y%m%d_%H%M%S_')
                                     + job_name + '.pickle')
    output_pickle_name = os.path.join(pickle_dir,
                                      strftime('output_%Y%m%d_%H%M%S_')
                                      + job_name + '.pickle')

    if verbose:
        print("Writing input pickle for job %s" % job_name)
    with open(input_pickle_name, 'wb') as input_pickle:
        pickle.dump(dict(fun=fun, fun_args=args, fun_kwargs=kwargs), input_pickle)

    # Make the python script for this job
    py_script = tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w')
    if verbose:
        print("Making py script pickle for job %s: %s" % (job_name, py_script.name))
    py_script.write(py_script_template.format(input_pickle_name=input_pickle_name,
                                              output_pickle_name=output_pickle_name,
                                              python_path=sys.executable))
    py_script.close()
    make_executable(py_script.name)

    # Submit the script to qsub
    # Now we'll learn our actual jobname from qsub, which we return
    cmd = submission_command_template.format(queue=queue,
                                             script_name=py_script.name,
                                             messages_dir=messages_dir,
                                             extra_options=extra_options,
                                             job_name=job_name)
    if verbose:
        print("qsub command for job %s: %s" % (job_name, cmd))
    job_name = subprocess.check_output(cmd, shell=True).decode('utf-8').rstrip()

    return job_name, output_pickle_name


def qsub_mapreduce(mapper, reducer, inputs,
                   pickle_dir=None, queue=default_queue, extra_options='', messages_dir=None,
                   delete_intermediate_pickles=True, verbose=False,
                   mapper_args=None, mapper_kwargs=None,
                   reducer_args=None, reducer_kwargs=None):
    """Make qsub jobs to execute reducer([mapper(inp) for inp in inputs]), return reducer jobname and output pickle.
    Each call to mapper and the final call to reducer happens in a separate job.
    The reducer job only starts when all of the mapper jobs are finished. Results are written to pickle files.

    :param mapper: callable. Will receive input as the first argument.
    :param reducer: callable. Will receive list of results from mappers as first argument.
    :param inputs: iterable. Each element will be passed to a separate mapper job
    :param pickle_dir: will be used to exchange input/output via pickles. Defaults to os.cwd() / qsub_pickles
    :param queue: name of the queue qsub will submit the job to
    :param extra_options: will be passes directly to the qsub command.
    :param messages_dir: will contain the files with stdout and stderr from jobs. Defaults to os.cwd() / qsub_messages
    :param delete_intermediate_pickles: if True(default), pickles produces by mappers will be deleted by reducer.
    :param verbose: if True, will print status information during job description.
    :param mapper_args: extra args passed to mapper function (after the first argument, which is one of inputs)
    :param mapper_kwargs: extra kwargs passed to mapper function
    :param reducer_args: extra args passed to reducer function (After the first argument, which is the results list)
    :param reducer_kwargs: extra kwargs passed to mapper function
    :return: qsub jobname of reducer, filename of output pickle file
    """
    if verbose:
        print("Starting submission of mapper jobs")

    # Submit the mapper jobs
    job_names = []
    job_pickles = []
    args = mapper_args if mapper_args is not None else []
    kwargs = mapper_kwargs if mapper_kwargs is not None else {}
    for inp in inputs:
        n, p = qsubwrap(mapper, inp, *args,
                              queue=queue, extra_options=extra_options,
                              pickle_dir=pickle_dir, messages_dir=messages_dir,
                              verbose=verbose,
                              **kwargs)
        job_names.append(n)
        job_pickles.append(p)

    def reducer_wrapper(job_pickles, delete_intermediate_pickles=delete_intermediate_pickles):
        """Load, then perhaps delete each of the pickles"""
        input_list = []
        for jp in job_pickles:
            with open(jp, 'rb') as q:
                input_list.append(pickle.load(q))
            if delete_intermediate_pickles:
                os.remove(jp)
        return reducer(input_list)

    if verbose:
        print("Starting submission of reducer job")
    args = reducer_args if reducer_args is not None else []
    kwargs = reducer_kwargs if reducer_kwargs is not None else {}
    reduce_jobname, reduce_pickle = qsubwrap(reducer_wrapper, job_pickles, *args,
                                                   extra_options='-m ae -W umask=0133,'
                                                                 'depend=afterok:' + ':'.join(job_names),
                                                   queue=queue, verbose=verbose,
                                                   pickle_dir=pickle_dir, messages_dir=messages_dir,
                                                   **kwargs)

    return reduce_jobname, reduce_pickle


def make_executable(path):
    """Make the file on path executable
    Stolen from some stackoverflow answer
    """
    mode = os.stat(path).st_mode
    mode |= (mode & 0o444) >> 2    # copy R bits to X
    os.chmod(path, mode)


if __name__ == '__main__':
    def find_partial_answer(i):
        return (i + 1.5)**2

    def combine_results(x):
        return 1 + sum(x)

    reducer_job, reducer_pickle = qsub_mapreduce(mapper=find_partial_answer,
                                                 inputs=range(1),
                                                 reducer=combine_results)

    print("Reducer job: %s\nReducer output pickle: %s" % (reducer_job, reducer_pickle))
