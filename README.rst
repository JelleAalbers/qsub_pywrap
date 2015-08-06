qsub_pywrap
===========
`https://github.com/JelleAalbers/qsub_pywrap`

Execute python functions as qsub jobs.

**Simple job submission**::

    from qsub_pywrap import qsubwrap

    def find_answer():
        return 42
        
    jobname, output_pickle = qsubwrap(find_answer, queue='yourqueue')

When the job is done, the result will be in a pickle with filename output_pickle. Extra args/kwargs passed to qsubwrap will be passed to your function. (except if they're one of the options to qsubwrap, such as verbose, pickle_dir, messages_dir, ... see docstring).

**Mapreduce functionality**::

    def find_partial_answer(i):
        return (i + 1.5)**2

    def combine_results(x):
        return 1 + sum(x)

    reducer_job, reducer_pickle = qsub_mapreduce(mapper=find_partial_answer,
                                                 inputs=range(4),
                                                 reducer=combine_results)


Each call to mapper and the final call to reducer will happen in a separate job. The reducer job only starts when all of the mapper jobs are finished, and the results will be written to reducer_pickle. See the docstring for the various options of qsub_mapreduce, which e.g. allow you to pass extra arguments to the mapper and reducer.
    
    
Alternatives
------------
A package with similar features is torque-submit `https://pypi.python.org/pypi/torque-submit/0.0.3`. This makes use of environment variables to pass data to jobs, and has quite a different interface. Documentation/docstrings are mostly absent.

If you just want to submit jobs that call a separate script or program, there are many, many alternatives: just google "qsub py" or "python qsub" and pick your favourite.

If you want detailed control over PBS jobs, you want pbs_python: `https://oss.trac.surfsara.nl/pbs_python`.




