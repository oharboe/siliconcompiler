# Copyright 2020 Silicon Compiler Authors. All Rights Reserved.
import siliconcompiler
import pytest

@pytest.fixture
def chip():
    # Create instance of Chip class
    chip = siliconcompiler.Chip('oh_add')

    #sequence
    flowpipe = ['import',
                'syn',
                'synmin']

    tools = {
        'import': 'verilator',
        'syn': 'yosys'
    }

    N = 10
    flow = 'testflow'
    chip.set('option', 'flow', flow)

    threads = {
        'import': 1,
        'syn' : N,
        'synmin' : 1
    }

    # Parallel flow for syn
    for i, step in enumerate(flowpipe):
        for index in range(threads[step]):
            if step == "synmin":
                chip.set('flowgraph', flow, step, str(index), 'tool', 'minimum')
                for j in range(N):
                    chip.add('flowgraph', flow, step, '0', 'input', (flowpipe[i-1],str(j)))
            elif step == 'import':
                chip.set('flowgraph', flow, step, str(index), 'tool', tools[step])
            else:
                chip.set('flowgraph', flow, step, str(index), 'tool', tools[step])
                chip.set('flowgraph', flow, step, str(index), 'input', (flowpipe[i-1],'0'))
            #weight
            chip.set('flowgraph', flow, step, str(index), 'weight', 'cellarea', 1.0)
            #goal
            chip.set('flowgraph', flow, step, str(index), 'goal', 'setupwns', 0.0)
            chip.set('metric', step, str(index), 'setupwns', 0.0)

    # creating fake syn results
    for index in range(N):
        for metric in chip.getkeys('flowgraph', flow, 'syn', str(index), 'weight'):
            chip.set('metric', 'syn', str(index), metric, 1000-index*1 + 42.0)

    return chip

##################################
def test_minimum(chip):
    '''API test for min/max() methods
    '''
    flow = chip.get('option', 'flow')
    N = len(chip.getkeys('flowgraph', flow , 'syn'))

    chip.write_flowgraph('minmax.png')
    chip.write_manifest('minmax.json')

    steplist = []
    for i in range(N):
        steplist.append(('syn',str(i)))
    (score, winner) = chip.minimum(*steplist)
    assert winner[0] + winner[1] == 'syn9'

def test_maximum(chip):
    flow = chip.get('option', 'flow')
    N = len(chip.getkeys('flowgraph', flow, 'syn'))

    steplist = []
    for i in range(N):
        steplist.append(('syn',str(i)))

    (score, winner) = chip.maximum(*steplist)
    assert winner == ('syn', '0')

def test_all_failed(chip):
    flow = chip.get('option', 'flow')
    N = len(chip.getkeys('flowgraph', flow, 'syn'))

    for index in range(N):
        chip.set('flowgraph', flow, 'syn', str(index), 'status', siliconcompiler.TaskStatus.ERROR)

    steplist = []
    for i in range(N):
        steplist.append(('syn',str(i)))

    (score, winner) = chip.minimum(*steplist)

    assert winner is None

def test_winner_failed(chip):
    flow = chip.get('option', 'flow')
    N = len(chip.getkeys('flowgraph', flow, 'syn'))

    # set error bit on what would otherwise be winner
    chip.set('flowgraph', flow, 'syn', '9', 'status', siliconcompiler.TaskStatus.ERROR)

    steplist = []
    for i in range(N):
        steplist.append(('syn',str(i)))

    (score, winner) = chip.minimum(*steplist)

    # winner should be second-best, not syn9
    assert winner[0] + winner[1] == 'syn8'

def test_winner_fails_goal_negative(chip):
    flow = chip.get('option', 'flow')
    N = len(chip.getkeys('flowgraph', flow, 'syn'))

    chip.set('metric', 'syn', '9', 'setupwns', -1)

    steplist = []
    for i in range(N):
        steplist.append(('syn',str(i)))

    (score, winner) = chip.minimum(*steplist)

    # winner should be second-best, not syn9
    assert winner == ('syn', '8')

def test_winner_fails_goal_positive(chip):
    flow = chip.get('option', 'flow')
    N = len(chip.getkeys('flowgraph', flow, 'syn'))

    chip.set('flowgraph', flow, 'syn', '9', 'goal', 'errors', 0)
    chip.set('metric', 'syn', '9', 'errors', 1)

    steplist = []
    for i in range(N):
        steplist.append(('syn',str(i)))

    (score, winner) = chip.minimum(*steplist)

    # winner should be second-best, not syn9
    assert winner == ('syn', '8')
