#!/usr/bin/env python
import os
import numpy as np

if __name__ == '__main__':
  from pyscf.pbc import gto
  from pyscf.pbc.scf import RHF
  from qharv.cross import pqscf
  import sys
  sys.path.insert(0,'../basis')
  from basis import bfd_basis

  mygs  = 16 # grid density

  # grid density for visualization
  myvgs = 6
  vgs = np.array([myvgs]*3)
  grid_shape = 2*vgs + 1

  # define isosurface levels
  default_up = 0.75
  default_dn = 0.25
  up_dn_map  = {
   0:{'up':0.9,'dn':-.1},
   1:{'up':0.6,'dn':0.3},
   3:{'up':0.65,'dn':0.3},
  }

  chkfile_fname = 'bfd.h5'
  moR_fname     = 'moR.dat'
  rho_fname     = 'rho.dat'
  alat0 = 3.6
  axes  = (np.ones((3,3))-np.eye(3))*alat0/2.0
  elem  = ['C','C']
  pos   = np.array([[0,0,0],[0.5,0.5,0.5]])*alat0
  atoms = pqscf.atom_text(elem,pos)

  gs    = np.array([mygs]*3)
  basis = bfd_basis()

  cell = gto.M(a=axes,atom=atoms,verbose=3
    ,gs=gs,pseudo={'C':'bfd'},basis=basis)
  mf = RHF(cell)
  mf.chkfile  = chkfile_fname
  mf.conv_tol = 1e-6

  # run or load RHF
  if os.path.isfile(chkfile_fname):
    from pyscf import lib
    mf.__dict__.update(lib.chkfile.load(chkfile_fname,'scf'))
  else:
    mf.kernel()
  # end if

  # grid density for molecular orbital
  mydgs = 16
  dgs = np.array([mydgs]*3)
  moR_fname = 'gs%d_'%mydgs+moR_fname
  # run or load moR
  if os.path.isfile(moR_fname):
    moR = np.loadtxt(moR_fname)
  else:
    from pyscf.pbc.gto.cell import gen_uniform_grids
    from pyscf.pbc.dft.numint import eval_ao
    coords = gen_uniform_grids(cell,gs=dgs)
    aoR    = eval_ao(cell,coords)
    moR    = np.dot(aoR,mf.mo_coeff)
    np.savetxt(moR_fname,moR)
  # end if

  mo_to_plot = [0,1,3,4]
  from qharv.inspect import volumetric
  from skimage import measure
  for iorb in mo_to_plot:

    val = moR[:,iorb].reshape(2*dgs+1)
    fval= volumetric.spline_volumetric(val)
    grid= volumetric.axes_func_on_grid3d(axes,fval,grid_shape)

    myup = default_up
    mydn = default_dn
    if iorb in up_dn_map.keys():
      myup = up_dn_map[iorb]['up']
      mydn = up_dn_map[iorb]['dn']
    # end if

    lmin,lmax = grid.min(),grid.max()
    levelup = lmin+myup*(lmax-lmin)
    leveldn = lmin+mydn*(lmax-lmin)

    if levelup > 0:
      verts,faces,normals,values = measure.marching_cubes_lewiner(grid,levelup)
      text = volumetric.wavefront_obj(verts,faces.astype(int),normals)
      with open('orb%d_up.obj'%iorb,'w') as f:
        f.write(text)
    if leveldn > 0:
      verts,faces,normals,values = measure.marching_cubes_lewiner(grid,leveldn)
      text = volumetric.wavefront_obj(verts,faces,normals)
      with open('orb%d_dn.obj'%iorb,'w') as f:
        f.write(text)
  # end for iorb

# end __main__
