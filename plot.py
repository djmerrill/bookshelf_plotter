import matplotlib
matplotlib.use('Agg')
from matplotlib import patches
import matplotlib.pyplot as plt
import sys

import shapely
from shapely import geometry

import numpy as np
import load_bookshelf

def plot_circuit(circuit_name, components, comp2rot, nets, board_dim,figname=None, stats = None):
	"""
	board dim: [[xs],[ys]]
	"""
	board_lower_left_corner = [min(board_dim[0]), min(board_dim[1])]
	board_upper_right_corner = [max(board_dim[0]), max(board_dim[1])]

	fig, ax = plt.subplots(1)
	if stats is None:
		ax.set_title(circuit_name)
	else:
		ax.set_title("circuit: " + circuit_name+ " wirelength: " + str(round(stats[0],2)) + " overlap: " + str(round(stats[1],2)))
	boundary = patches.Rectangle((min(board_dim[0]), min(board_dim[1])), \
								  max(board_dim[0]) - min(board_dim[0]), max(board_dim[1]) - min(board_dim[1]), \
								  linewidth=1,edgecolor='b',facecolor='none')
	ax.add_patch(boundary)
	for name,shape in components.items():
		if isinstance(shape, geometry.Point):
			x = shape.x
			y = shape.y
			ax.scatter(x,y, c='b',s=5)
			label = ax.annotate(name, xy=(x, y), fontsize=5, ha="right", va="top", )
		else:
			x, y = shape.exterior.coords.xy
			c = shape.centroid
			points = np.array([x, y], np.int32).T
			polygon_shape = patches.Polygon(points, linewidth=1, edgecolor='r', facecolor='none')
			ax.add_patch(polygon_shape)
			label = ax.annotate(name, xy=(c.x, c.y), fontsize=5, ha="right", va="top")

	# draw nets
	for net in nets:
		netlist = []
		c = [np.random.rand(3)] # random color
		for pin in net:
			if pin[0] not in components:
				try:
					cx = pin[1].x
					cy = pin[1].y
				except:
					cx = pin[1][0]
					cy = pin[1][1]
			else:
				cx, cy = pin_pos2(pin,components,comp2rot)
			netlist.append([cx,cy])
		xmax = max([p[0] for p in netlist])
		xmin = min([p[0] for p in netlist])
		ymax = max([p[1] for p in netlist])
		ymin = min([p[1] for p in netlist])
		center =  [(xmax + xmin)/2,(ymax + ymin)/2]
		for i in range(len(netlist)):
			ax.plot([netlist[i][0],center[0]],[netlist[i][1],center[1]], color=tuple(map(tuple, c))[0] + (255,), linewidth=1, alpha=0.25, linestyle='dashed')
		xs= [ x[0] for x in netlist ]
		ys= [ x[1] for x in netlist ]
		ax.scatter(xs,ys,marker='.',c=c)
		ax.scatter(center[0],center[1],marker='.',c=c)
	plt.xlim(board_lower_left_corner[0] - 50,board_upper_right_corner[0] + 50)
	plt.ylim(board_lower_left_corner[1] - 50,board_upper_right_corner[1] + 50)
	plt.gca().set_aspect('equal', adjustable='box')
	#plt.show()
	if figname:
		plt.savefig(figname)
	else:
		plt.show()

def pin_pos2(pin_loc, modules,comp2rot):
	"""
	Convert localized pin positions to position wrt
	 global coordinates
	:param pin_loc: pin location of the form [pinname, [xoffset, yoffset]]
	:param modules: list of modules
	"""
	module_name, local_pin_loc = pin_loc
	cx = modules[module_name].centroid.x
	cy = modules[module_name].centroid.y
	if module_name in comp2rot:
		r = comp2rot[module_name]
	else:
		r = 'N'
	if r == 'N':
		pinx = cx + local_pin_loc[0]
		piny = cy + local_pin_loc[1]
	elif r == 'S':
		pinx = cx - local_pin_loc[0]
		piny = cy - local_pin_loc[1]
	elif r == 'E':
		pinx = cx - local_pin_loc[1]
		piny = cy + local_pin_loc[0]
	elif r == 'W':
		pinx = cx + local_pin_loc[1]
		piny = cy - local_pin_loc[1]

	return pinx, piny

def pin_pos(pin_loc, modules):
	"""
	Convert localized pin positions to position wrt
	 global coordinates
	:param pin_loc: pin location of the form [pinname, [%x, %y]]
	:param modules: list of modules
	"""
	module_name, local_pin_loc = pin_loc
	minx, miny, maxx, maxy = modules[module_name].bounds

	pinx = (maxx - minx) * local_pin_loc[0] + minx
	piny = (maxy - miny) * local_pin_loc[1] + miny
	return pinx, piny

"""
arg 1: dir/circuitname
arg 2: bookshelf version (0,1) = (old,new)
arg 3: figname

optional
arg 4: min plot dimension
arg 5: max plot dimension
"""
circuitname = sys.argv[1]
plfile = circuitname + '.pl'
nodesfile = circuitname + '.nodes'
netsfile = circuitname + '.nets'
bversion = int(sys.argv[2])
boarddim = None
figname = sys.argv[3]
if len(sys.argv) > 4:
	boarddimmin = int(sys.argv[4])
	boarddimmax = int(sys.argv[5])

if bversion == 0: # old version of bookshelf
	components, board_pins = load_bookshelf.read_pl(plfile)
	nets,mod2net = load_bookshelf.read_nets(netsfile,components,board_pins)
	if board_pins is not None and len(board_pins) > 0:
		xs = [pin[1].x for pin in board_pins.items()]
		ys = [pin[1].y for pin in board_pins.items()]
		board_dim = [xs,ys]
	else:
		board_dim = [[-500,500],[-500,500]]
	plot_circuit(plfile.split('.')[0], components,{},nets,board_dim,figname)
elif bversion == 1: # new version of bookshelf
	#components,_ = load_bookshelf.read_pl(plfile)
	components = load_bookshelf.read_nodes(nodesfile)
	components,comp2rot,board_pins = load_bookshelf.read_pl2(plfile,components)
	nets,mod2net = load_bookshelf.read_nets2(netsfile,components,board_pins)

	if boarddimmin is None:
		if board_pins is not None and len(board_pins) > 0:
			xs = [pin[1].x for pin in board_pins.items()]
			ys = [pin[1].y for pin in board_pins.items()]
			board_dim = [xs,ys]
		else:
			board_dim = [[-500,500],[-500,500]]
	else:
		board_dim = [[boarddimmin,boarddimmax],[boarddimmin, boarddimmax]]
	plot_circuit(plfile.split('.')[0], components,comp2rot,nets,board_dim,figname)

else:
	print('bookshelf version must be 0 or 1')
