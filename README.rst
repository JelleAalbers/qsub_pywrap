qsub_pywrap
===========
`https://github.com/JelleAalbers/qsub_pywrap`

Execute python functions as qsub jobs.

Simplest example::
    from qsub_pywrap import qsubwrap

    def find_answer():
        return 42
        
    jobname, output_pickle = qsubwrap(find_answer, queue='yourqueue')

When the job is done, the result will be in a pickle with filename output_pickle. You can check the status ofExtra args/kwargs passed to qsubwrapped will be passed to your function. (except if they're one of the options to qsubwrap, such as verbose, pickle_dir, messages_dir, ... see docstring).

Mapreduce-like example::

    def find_partial_answer(i):
        return (i + 1.5)**2

    def combine_results(x):
        return 1 + sum(x)

    reducer_job, reducer_pickle = qsub_mapreduce(mapper=find_partial_answer,
                                                 inputs=range(4),
                                                 reducer=combine_results)

    
Alternatives
------------
A package with similar features is torque-submit `https://pypi.python.org/pypi/torque-submit/0.0.3`. This makes use of environment variables to pass data to jobs, and has quite a different interface. Documentation/docstrings are mostly absent.

If you just want to submit jobs that call a separate script or program, there are many, many alternatives: just google "qsub py" or "python qsub" and pick your favourite.

If you want detailed control over PBS jobs, you want pbs_python: `https://oss.trac.surfsara.nl/pbs_python`.



