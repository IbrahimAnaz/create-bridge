import json, re

data = json.load(open('headless_server/create_detailed_blockstates.json'))
pipe_states = data['create:fluid_pipe']

shapes = {}

for state_str, raw_id in pipe_states.items():
    # parse properties
    # Block{create:fluid_pipe}[down=true,east=true,north=true,south=true,up=true,waterlogged=true,west=true]
    props = dict(re.findall(r'([a-z]+)=([a-z]+)', state_str))
    down = props.get('down') == 'true'
    up = props.get('up') == 'true'
    north = props.get('north') == 'true'
    south = props.get('south') == 'true'
    east = props.get('east') == 'true'
    west = props.get('west') == 'true'
    
    conns = [k for k, v in [('down', down), ('up', up), ('north', north), ('south', south), ('east', east), ('west', west)] if v]
    num_conns = len(conns)
    
    shape = "none"
    if num_conns == 0:
        shape = "hub"
    elif num_conns == 1:
        shape = f"single_{conns[0]}"
    elif num_conns == 2:
        if up and down:
            shape = "straight_y"
        elif east and west:
            shape = "straight_x"
        elif north and south:
            shape = "straight_z"
        else:
            shape = f"elbow_{conns[0]}_{conns[1]}"
    elif num_conns >= 3:
        shape = f"junction_{num_conns}"
    
    shapes.setdefault(shape, []).append((state_str, raw_id))

print(f"Total pipe states: {len(pipe_states)}")
for s, lst in sorted(shapes.items()):
    print(f"  {s}: {len(lst)} states (example: raw_id {lst[0][1]})")
