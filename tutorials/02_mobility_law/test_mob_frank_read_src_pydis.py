import numpy as np
import sys, os

pydis_paths = ['../../python', '../../lib', '../../core/pydis/python', '../../core/exadis/python']
[sys.path.append(os.path.abspath(path)) for path in pydis_paths if not path in sys.path]
np.set_printoptions(threshold=20, edgeitems=5)

from framework.disnet_manager import DisNetManager
from pydis import DisNode, DisNet, Cell, CellList
from pydis import CalForce, TimeIntegration
from pydis import Collision, Remesh, VisualizeNetwork, SimulateNetwork

from user_mob_bccglide import My_MobilityLaw, My_Topology

def init_frank_read_src_loop(arm_length, box_length, burg_vec, plane_norm, pbc=True):
    '''Generate an initial Frank-Read loop configuration
    Set the Buerges vector along the x-direction, dislocation line 
    along the y-direction and plane normal along the z-direction.
    '''
    print("init_frank_read_src_loop: length = %f" % (arm_length))
    cell = Cell(h=box_length*np.eye(3), is_periodic=[pbc,pbc,pbc])
    
    # crystal orientation matrix
    plane = plane_norm / np.linalg.norm(plane_norm)
    b = burg_vec / np.linalg.norm(burg_vec)
    y = np.cross(plane, b)
    y = y / np.linalg.norm(y)
    linedir = np.cos(np.pi/2.0)*b+np.sin(np.pi/2.0)*y
    x = np.cross(linedir, plane)
    x = x / np.linalg.norm(x)
    Rorient = np.array([x, linedir, plane])
    
    burg_vec = np.matmul(Rorient, burg_vec)
    plane_norm = np.matmul(Rorient, plane_norm)
    linedir = -np.matmul(Rorient, linedir)
    
    rn    = np.array([[0.0, -arm_length/2.0, 0.0,         DisNode.Constraints.PINNED_NODE],
                      [0.0,  0.0,            0.0,         DisNode.Constraints.UNCONSTRAINED],
                      [0.0,  arm_length/2.0, 0.0,         DisNode.Constraints.PINNED_NODE],
                      [0.0,  arm_length/2.0, -arm_length, DisNode.Constraints.PINNED_NODE],
                      [0.0, -arm_length/2.0, -arm_length, DisNode.Constraints.PINNED_NODE]])
    rn[:,0:3] += cell.center()

    N = rn.shape[0]
    links = np.zeros((N, 8))
    for i in range(N):
        pn = np.cross(burg_vec, rn[(i+1)%N,:3]-rn[i,:3])
        pn = pn / np.linalg.norm(pn)
        links[i,:] = np.concatenate(([i, (i+1)%N], burg_vec, pn))

    net = DisNetManager(DisNet(cell=cell, rn=rn, links=links))
    return net, Rorient


def main():
    global net, sim, state

    Lbox = 1000.0
    
    # 1/2<111>{110} dislocation
    burg_vec = 1.0/np.sqrt(3.0)*np.array([1.,1.,1.])
    plane_norm = np.array([1.,-1.,0.])
    
    net, Rorient = init_frank_read_src_loop(box_length=Lbox, arm_length=0.125*Lbox, burg_vec=burg_vec, plane_norm=plane_norm)
    
    nbrlist = CellList(cell=net.cell, n_div=[8,8,8])

    vis = VisualizeNetwork()
    
    state = {"crystal": 'bcc', "Rorient": Rorient,
             "burgmag": 3e-10, "mu": 50e9, "nu": 0.3, "a": 1.0, "maxseg": 0.04*Lbox, "minseg": 0.01*Lbox, "rann": 3.0,
             "mob": 1.0, "mob_edge": 1.0, "mob_screw": 0.1}

    calforce  = CalForce(force_mode='LineTension', state=state)
    mobility  = My_MobilityLaw(mobility_law='BCCGlide', state=state)
    timeint   = TimeIntegration(integrator='EulerForward', dt=1.0e-8, state=state)
    topology  = My_Topology(split_mode='MaxDiss', state=state, force=calforce, mobility=mobility)
    collision = Collision(collision_mode='Proximity', state=state, nbrlist=nbrlist)
    remesh    = Remesh(remesh_rule='LengthBased', state=state)

    sim = SimulateNetwork(calforce=calforce, mobility=mobility, timeint=timeint,
                          topology=topology, collision=collision, remesh=remesh, vis=vis,
                          state=state, max_step=1000, loading_mode="stress",
                          applied_stress=np.array([0.0, 0.0, 0.0, 0.0, -4.0e8, 0.0]),
                          print_freq=10, plot_freq=10, plot_pause_seconds=0.01,
                          write_freq=10, write_dir='output', save_state=False)
    sim.run(net, state)

    return net.is_sane()


if __name__ == "__main__":
    main()

    # explore the network after simulation
    G  = net.get_disnet()

    os.makedirs('output', exist_ok=True)
    net.write_json('output/frank_read_src_pydis_final.json')
