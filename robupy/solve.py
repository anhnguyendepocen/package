""" This module serves as the interface to the alternative implementations to
solve the model.
"""

# standard library
import shlex
import os

# project library
from robupy.fortran.solve_fortran import solve_fortran
from robupy.python.solve_python import solve_python
from robupy.simulate import simulate

''' Public function
'''


def solve(robupy_obj):
    """ Solve dynamic programming problem by backward induction.
    """
    # Antibugging
    assert (robupy_obj.get_status())

    # Cleanup
    cleanup()

    # Distribute class attributes
    is_ambiguous = robupy_obj.get_attr('is_ambiguous')

    version = robupy_obj.get_attr('version')

    is_debug = robupy_obj.get_attr('is_debug')

    store = robupy_obj.get_attr('store')

    # Select appropriate interface
    if version == 'FORTRAN':

        robupy_obj = solve_fortran(robupy_obj)

    else:

        robupy_obj = solve_python(robupy_obj)

    # Summarize optimizations in case of ambiguity.
    if is_debug and is_ambiguous:
        _summarize_ambiguity(robupy_obj)

    # Set flag that object includes the solution objects.
    robupy_obj.unlock()

    robupy_obj.set_attr('is_solved', True)

    robupy_obj.lock()

    # Simulate model.
    simulate(robupy_obj)

    # Store results if requested
    if store:
        robupy_obj.store('solution.robupy.pkl')

    # Finishing
    return robupy_obj

''' Auxiliary functions
'''


def _summarize_ambiguity(robupy_obj):
    """ Summarize optimizations in case of ambiguity.
    """

    def _process_cases(list_):
        """ Process cases and determine whether keyword or empty line.
        """
        # Antibugging
        assert (isinstance(list_, list))

        # Get information
        is_empty = (len(list_) == 0)

        if not is_empty:
            is_block = list_[0].isupper()
        else:
            is_block = False

        # Antibugging
        assert (is_block in [True, False])
        assert (is_empty in [True, False])

        # Finishing
        return is_empty, is_block

    # Distribute class attributes
    num_periods = robupy_obj.get_attr('num_periods')

    dict_ = dict()

    for line in open('ambiguity.robupy.log').readlines():

        # Split line
        list_ = shlex.split(line)

        # Determine special cases
        is_empty, is_block = _process_cases(list_)

        # Applicability
        if is_empty:
            continue

        # Prepare dictionary
        if is_block:

            period = int(list_[1])

            if period in dict_.keys():
                continue

            dict_[period] = {}
            dict_[period]['success'] = 0
            dict_[period]['failure'] = 0

        # Collect success indicator
        if list_[0] == 'Success':
            is_success = (list_[1] == 'True')
            if is_success:
                dict_[period]['success'] += 1
            else:
                dict_[period]['failure'] += 1

    with open('ambiguity.robupy.log', 'a') as file_:

        file_.write('SUMMARY\n\n')

        string = '''{0[0]:>10} {0[1]:>10} {0[2]:>10} {0[3]:>10}\n'''

        file_.write(string.format(['Period', 'Total', 'Success', 'Failure']))

        file_.write('\n')

        for period in range(num_periods):
            success = dict_[period]['success']
            failure = dict_[period]['failure']
            total = success + failure

            file_.write(string.format([period, total, success, failure]))


def cleanup():
    """ Cleanup all selected files. Note that not simply all *.robupy.*
    files can be deleted as the blank logging files are already created.
    """
    try:
        os.unlink('ambiguity.robupy.log')
    except IOError:
        pass
