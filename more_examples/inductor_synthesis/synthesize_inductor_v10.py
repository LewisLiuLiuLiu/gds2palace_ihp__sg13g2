# Inductor synthesis for SG13G2 technology with inductor shapes from pclab, EM simulated using gds2palace workflow

import os, math, sys, time, shutil
import subprocess
from gds2palace import *
import skrf as rf
from matplotlib import pyplot as plt

# import inductor shape library, with some local bugfix
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'pclab')))
from pclab import *  # https://github.com/dgrujic/pcLab


# RUN CONTROLS
start_simulation = True # start solver after creating the model?
cleanup_old_data = True # cleanup existing GDSII and S-parameters when starting a new run?

initial_sweep_FEM_order = 1  # many candicates are simulated here, order=1 is faster but less accurate
finetune_FEM_order = 2  # user oder=2 for accurate results from finetune step

how_many_top_results = 2  # number of best inductors from initial sweep that are evaluated more closely and re-tuned to target
how_many_finetune_steps = 2 # how many iteration of tune-to-target before selecting the final candidate for full frequency sweep

# CREATE INDUCTOR WITH TARGET VALUE
Ltarget = 0.5e-9 # target inductance in H
ftarget = 40e9  # design frequency in Hz
faked_dc = 0.1e9  # do not change, this is the "DC-like" low frequency for data extraction

w_range = [2.01, 3,4,6,10,15,20] # sweep over these width values 
s_range = [2.01, 4,6]
nturns_range = [2]
dout_max = 300 # maximum outer diameter in microns

ind_geom = "octagon" # valid choices: "rect", "octagon"
layout_with_centertap = False # layout with or without center tap

feedline_length = 30 # Fixed value for IHP inductor 2/3 is 30 micron feed line length, so we use that here

# define inductor/balun geometry, 
# valid without center tap, or with center tap for nturns=1,2,4,6, ...
sig_lay = "TopMetal2"  # main layer for inductor/balun turns
underpass_lay = "TopMetal1"
centertap_layer = "TopMetal1" 

# Alternative mapping is required for center tap geometries 
# if we have odd number of turns (3, 5, ...)
sig_lay_CT = "TopMetal1"  # main layer for inductor/balun turns
underpass_lay_CT = "TopMetal2"
centertap_layer_CT = "Metal5" 


# configure ground frame for return current (shared port reference)
groundframe_layer = "Metal1"  # EM simulation ground frame = port reference node
frame_width = 30 #  Width of ground frame. 
frame_margin = 40 # Distance from inductor/balun geometry to inner side of ground frame.

# TECHNOLOGY
tech = Technology("SG13G2.tech")  # Technology for geometry creation using pclab
XML_filename = "SG13G2_200um.xml"   #  EM simulation stackup data       

# Calibration factors for inductor diameter calculation using modified Wheeler equation
# see table 1 here: https://web.stanford.edu/~boyd/papers/pdf/inductance_expressions.pdf
# Values below are specific for IHP SG13G2 technology
K1_octadiff = 2.15522
K2_octadiff = 3.61868
L0_octadiff = 0  # fixed inductance from feedlines

K1_squarediff = 2.456
K2_squarediff = 3.583
L0_squarediff = 0 # fixed inductance from feedlines


materials_list, dielectrics_list, metals_list = stackup_reader.read_substrate (XML_filename)


# ----------------------------------------------------------------

settings = {}

settings['unit']   = 1e-6  # geometry is in microns
settings['margin'] = 50    # distance in microns from GDSII geometry boundary to simulation boundary 

settings['fstart']  = ftarget
settings['fstop']   = ftarget
settings['fstep']   = 1e9
settings['fpoint']  = faked_dc

settings['preprocess_gds'] = True
settings['merge_polygon_size'] = 1.5

settings['refined_cellsize'] = 5  # mesh cell size in conductor region
settings['adaptive_mesh_iterations'] = 0  # Palace adative mesh iterations

settings['cells_per_wavelength'] = 10   # how many mesh cells per wavelength, must be 10 or more
settings['meshsize_max'] = 70  # microns, override cells_per_wavelength 

settings['no_gui'] = True  # create files without showing 3D model
settings['no_preview'] = True
settings['order'] = initial_sweep_FEM_order

script_path = utilities.get_script_path(__file__)  # get path for this simulation file


# ----------------------------------------------------------------

def create_simulation_model (gds_filename, settings, geometry_name, port_dict, port_layer):
    """Creates a Palace FEM simulation model from GDSII file using gds2palace

    Args:
        gds_filename (string): GDSII input file that also includes port geometries
        settings (dict): settings for gds2palace
        geometry_name (string): name for the Palace model
        port_dict (dict): dictionary with port information created by gds_pin2viaport function in pclab library
        port_layer (string): Layer name where upper end of port is connected

    Returns:
        config_name, data_dir: filename of Palace config.json file and output directory
    """

    # ======================== simulation settings ================================

    # create model basename from balun name and settings
    model_basename = geometry_name
    sim_path = utilities.create_sim_path (script_path,model_basename) # set and create directory for simulation output

    simulation_ports = simulation_setup.all_simulation_ports()
    # get ports that were created from pins in gds_pin2viaport() function
    # these are returned as dictionary: key is pin name, value is array [created port layer, pox x, pos y]
    for n, key in enumerate(port_dict.keys()):
        portnumber = n+1
        port_source_layer = port_dict[key][0]
        print(f'Pin {key} -> EM port {portnumber} on layer {port_source_layer}')

        simulation_ports.add_port(simulation_setup.simulation_port(portnumber=portnumber, 
                                                                voltage=1, 
                                                                port_Z0=50, 
                                                                source_layernum=port_source_layer, 
                                                                from_layername=groundframe_layer,
                                                                to_layername=port_layer, 
                                                                direction='z'))

    # ======================== read material stackup and geometry ================================

    # get list of layers from technology
    layernumbers = metals_list.getlayernumbers()
    layernumbers.extend(simulation_ports.portlayers)

    # read geometries from GDSII, only purpose 0
    allpolygons = gds_reader.read_gds(gds_filename, layernumbers, purposelist=[0], metals_list=metals_list, preprocess=settings['preprocess_gds'], merge_polygon_size=settings['merge_polygon_size'])


    ########### create model ###########

    settings['simulation_ports'] = simulation_ports
    settings['materials_list'] = materials_list
    settings['dielectrics_list'] = dielectrics_list
    settings['metals_list'] = metals_list
    settings['layernumbers'] = layernumbers
    settings['allpolygons'] = allpolygons
    settings['sim_path'] = sim_path
    settings['model_basename'] = model_basename


    # list of ports that are excited (set voltage to zero in port excitation to skip an excitation!)
    excite_ports = simulation_ports.all_active_excitations()
    config_name, data_dir = simulation_setup.create_palace (excite_ports, settings)

    # add palace config to list, we will simulate later in one action
    return config_name, data_dir

# -----------------------------------------------------------------

def run_models_from_list (script_path, config_files_list):
    """Create and run batch file that simulates all Plaace models from the given list

    Args:
        script_path (string): Target directory where to store batch script
        config_files_list (list of strings): list with filepath of Palace config.json for models to be simulated
    """
    # Create ONE script file in script_path to simulate ALL models
    # This is to avoid asynchronous finish of simulation jobs
    simulate_script_filename = os.path.join(script_path, 'simulate_all')
    output_file = open(simulate_script_filename, "w") 
    output_file.write('#!/bin/bash\n')
    output_file.write('START_DIR="$PWD"\n')
    for config_name in config_files_list:
        path, basename = os.path.split(config_name)
        output_file.write(f'cd {path}\n')
        output_file.write(f'run_palace {basename}\n')
    output_file.write('cd "$START_DIR"\n')
    # next step is to create Touchstone data
    output_file.write('combine_snp\n')
    # move *.snp to directory where Python model is 
    output_file.write(r'find . -type f -name "*.s*p" -exec cp {} . \;' + '\n')
    output_file.close() 

    if sys.platform.startswith("linux"):
        os.chmod(simulate_script_filename, 0o755)        
        if start_simulation:
            subprocess.run(simulate_script_filename, shell=True)


# -----------------------------------------------------------------

def check_if_model_valid(nturns, w, s, d_outer, layout_with_centertap):
    """Try to create a pclab geometry object for an inductor, wiuth given parameters

    Args:
        nturns (integer): number of turns
        w (float): width in micron
        s (float): spacing in micron
        d_outer (float): outer diameter in micron
        layout_with_centertap (Boolean): Centertap True/False

    Returns:
        valid, do_min, ind, port_layer: layout valid, minimum possible diameter, inductor created object, layer for + terminal of ports
    """
    if layout_with_centertap:
        ind = inductorSymCT(tech)
        if nturns<=2 or nturns % 2 == 0:
            # tap on underpass layer
            valid = ind.setupGeometry(d_outer, w, s, nturns, sig_lay, underpass_lay, centertap_layer, ind_geom, connectLen=feedline_length)        
            port_layer =  sig_lay    # target for EM port       
        else:
            # alternative layer mapping required where coil is between tap layer and underpass/overpass layer
            valid = ind.setupGeometry(d_outer, w, s, nturns, sig_lay_CT, underpass_lay_CT, centertap_layer_CT, ind_geom, connectLen=feedline_length)
            port_layer = sig_lay_CT  # target for EM port      
    else:
        ind = inductorSym(tech)    
        valid = ind.setupGeometry(d_outer, w, s, nturns, sig_lay, underpass_lay, ind_geom, connectLen=feedline_length)
        port_layer = sig_lay  # target for EM port      

    do_min = ind.get_min_diameter() # minimum allowed diameter
    return valid, do_min, ind, port_layer


def create_gds_and_model (nturns, w, s, d_outer, layout_with_centertap, remove_centertap_for_EM):
    """Create GDSII file and Palace model from given parameters

    Args:
        nturns (integer): number of turns
        w (float): width in micron
        s (float): spacing in micron
        d_outer (float): outer diameter in micron
        layout_with_centertap (Boolean): Centertap True/False
        remove_centertap_for_EM (Boolean): If True, no EM port is created for a center tap 

    Returns:
        If layout is possible: config_name, data_dir, port_dict, geometry_name, do_min: Palace config file, Palace output dir, port dict, model name, minimum possible diameter
        If layout is not possible: None, None, None, None, do_min
    """
    # create layout file, convert to layout file with ports, then run gds2palace to create simulation model

    valid, do_min, ind, port_layer = check_if_model_valid(nturns, w, s, d_outer, layout_with_centertap)

    if valid:
        geometry_name = f"indSym_{ind_geom}_N{nturns}_do{d_outer}_w{w}_s{s}"
        ind.genGeometry()
        gds_filename = geometry_name + '.gds'
        ind.genGDSII(gds_filename, structName = gds_filename)
        print(f"Created output file {gds_filename}")

        # Create derived GDSII file where pins are converted to EM ports for gds2palace flow
        # We want to draw ground frame on layer Metal1, get the GDSII layer number 
        frame_layernum = int(metals_list.getbylayername (groundframe_layer).layernum)
        port_dict = gds_pin2viaport(gds_filename, width=w, port_layer_start=201, add_frame=True, frame_layer=frame_layernum, frame_width = frame_width, frame_margin=frame_margin)

        # check if we have a centertap, then check if we want to include that in EM simulation
        if 'CT' in port_dict.keys():
            if remove_centertap_for_EM:
                del port_dict['CT']

        # continue from the modified GDSII file that includes ports
        gds_filename = gds_filename.replace(".gds","_forEM.gds")

        # create Palace model and add to list of models, but don't start simulation immediately
        config_name, data_dir = create_simulation_model (gds_filename, settings, geometry_name, port_dict, port_layer)
        return config_name, data_dir, port_dict, geometry_name, do_min
    else:
        print(f'Skip invalid diameter, minimimum possible diameter is {do_min}')
        return None, None, None, None, do_min



def create_models_from_list (geometry_candidates_list, layout_with_centertap, remove_centertap_for_EM):
    """Create GDSII files and Palace models from a list of geometry parameters

    Args:
        geometry_candidates_list (list): List of geometry parameters
        layout_with_centertap (Boolean): Inductor layout has centertap
        remove_centertap_for_EM (Boolean): Do not create extra port for possible center tap 

    Returns:
        palace_config_files, all_models_dict, data_dir, port_dict
    """
    # create GDSII and Palace model from list of geometry candidates

    palace_config_files = []  # the created config.json with full path
    all_models_dict = {} # name and data of models, used so that we can find "our" results later
    data_dir = None
    port_dict = None

    for geometry in geometry_candidates_list:
        nturns = geometry['nturns']
        w = geometry['w']
        s = geometry['s']
        d_outer = geometry['d_outer']

        config_name, a_data_dir, a_port_dict, geometry_name, do_min = create_gds_and_model (nturns, w, s, d_outer, layout_with_centertap, remove_centertap_for_EM)
        if config_name is not None:
            palace_config_files.append(config_name)  
            model_data_dict = {'nturns':nturns, 'w':w, 's':s, 'd_outer':d_outer} 
            all_models_dict[geometry_name] = model_data_dict
            data_dir = a_data_dir
            port_dict = a_port_dict    

    return palace_config_files, all_models_dict, data_dir, port_dict


def get_best_results (palace_config_files, requested_result_count, all_models_dict, port_dict, rescale_diameter=True):
    """after simulation, read results and calculate new rescaled diameter for next iteration
    then, sort results by Q factor and return the requested_result_count best geometries

    Args:
        palace_config_files (list): list of Palace config.json files
        requested_result_count (Integer): How many toop results are returned
        all_models_dict (dict): geometry parameters for inductors from list
        port_dict (dict): Port configuration created by gds_pin2viaport for each layout
        rescale_diameter (bool, optional): Re-calculate outer diameter for next iteration? Defaults to True.

    Returns:
        _type_: _description_
    """
    # after simulation, read results and calculate new rescaled diameter for next iteration
    # then, sort results by Q factor and return the requested_result_count best geometries

    num_ports = len(port_dict) # we need port count to set correct Touchstone suffix
    expected_snp_results = []
    for model_name in all_models_dict.keys():
        snp_name = f"{model_name}.s{num_ports}p"
        # only append files that actually exist
        if os.path.isfile(snp_name):
            expected_snp_results.append(snp_name)

    # now read all these files
    networks = []
    for snp_file in expected_snp_results:
        network = rf.Network(snp_file)
        networks.append(network)

    results_dict = {}
    

    for network in networks:
        nturns = all_models_dict[network.name]['nturns']
        w = all_models_dict[network.name]['w']
        s = all_models_dict[network.name]['s']
        d_outer = all_models_dict[network.name]['d_outer']

        freq, Rdiff, Ldiff, Qdiff = get_diff_model(network)
        # get data at target frequency
        ftarget_index = rf.find_nearest_index(freq, ftarget)
        L_at_ftarget = Ldiff[ftarget_index]
        Q_at_ftarget = Qdiff[ftarget_index]

        # get data at faked DC point
        DC_index = rf.find_nearest_index(freq, faked_dc)
        L_at_DC = Ldiff[DC_index]
        # calculate tweaked new diameter to reach target value
        resize_factor = calc_resize_factor (Ltarget, L_at_ftarget, L_at_DC)
        d_outer_new = math.ceil(d_outer*resize_factor*100)/100  # 2 decimal digits only

        if rescale_diameter:
            d_outer = d_outer_new

        # add to dictionary of results, not sorted at this moment
        results_dict[Q_at_ftarget] = {'nturns':nturns,'w':w,'s':s,'d_outer':d_outer}
        # write to log
        log.append(f"  {network.name}: L={L_at_ftarget*1e9:.2f}nH Q={Q_at_ftarget:.1f}, parameters N={nturns} w={w} s={s} do={d_outer} -> {d_outer_new}")

    # sort results by Q factor, get best 
    sorted_results = dict(sorted(results_dict.items(), key=lambda item: int(item[0]), reverse=True))

    # write to top list
    geometries =[]
    for geometry in sorted_results.values():
            geometries.append(geometry)
    if requested_result_count > len(geometries):        
        best_list = geometries[:requested_result_count] 
    else:
        best_list = geometries            
    return best_list
    

# -----------------------------------------------------------------

# function to get differential Zin from one- or two-port data

def get_diff_model (sub):
    """Get differential inductor parameters from 2-port data

    Args:
        sub (network): network to evaluate

    Returns:
        freq, Rdiff, Ldiff, Qdiff
    """
    if sub.number_of_ports == 1:
        Zdiff=sub.z[0::,0,0]
    elif sub.number_of_ports == 2:
        z11=sub.z[0::,0,0]
        z21=sub.z[0::,1,0]
        z12=sub.z[0::,0,1]
        z22=sub.z[0::,1,1]
        Zdiff = z11-z12-z21+z22
    else:
        print('S-parameter files with ', sub.number_of_ports, ' ports not supported')
        exit(1)    
    
    freq = sub.frequency.f
    omega = freq*2*math.pi
    Ldiff = Zdiff.imag/omega
    Rdiff = Zdiff.real
    Qdiff = Zdiff.imag/Zdiff.real
    
    return freq, Rdiff, Ldiff, Qdiff


def calc_resize_factor (L_target, L_is_ftarget, L_is_DC):
    """finetune step: rescale diameter after initial simulation that was based on predicted DC inductance
    make sure L_is_ftarget is positive, it might be negative if we are above SRF -> drop this geometry

    Args:
        L_target (float): target inductance that we want to reach
        L_is_ftarget (float): simulated inductance at target frequency
        L_is_DC (float): simulated inductance at DC-like low frequency

    Returns:
        float: scaling factor for diameter resize 
    """
    # finetune step: rescale diameter after initial simulation that was based on predicted DC inductance
    # make sure L_is_ftarget is positive, it might be negative if we are above SRF -> drop this geometry
    if L_is_ftarget>0:
        factor = math.pow(L_target/L_is_ftarget, 0.5)
    else:
        factor = 1000 # will result in dropping geometry    

    return factor

# -----------------------------------------------------------------
#    MAIN
# -----------------------------------------------------------------

# CLEANUP OLD DATA BEFORE WE CREATE NEW INDUCTOR

if cleanup_old_data:
    # cleanup old models
    if sys.platform.startswith("linux"):
        os.system('rm -rf palace_model')
        os.system('rm -f *.s?p *.gds')

time.sleep(1)

global log
log = []
log.append(f'Design goal: {ind_geom} L={Ltarget*1e9} nH @ {ftarget/1e9} GHz ')


# CREATE MODELS FOR INITIAL SWEEP ACROSS ALL CANDIDATES

geometry_candidates_list = []
for nturns in nturns_range:  # number of turns
    for w in w_range:  # trace width
        
        # for special case N=1, we don't need to sweep over multiple spacing values
        if nturns>1:
            s_sweep = s_range
        else:
            s_sweep = [0]
                
        for s in s_sweep:  # spacing between turns

            # calculate diameter from target inductance
            if ind_geom == "octagon":
                d_outer = calculate_octa_diameter (nturns, w, s, Ltarget, K1=K1_octadiff, K2=K2_octadiff, L0=L0_octadiff)  # technology specific, for generic technology remove parameters K1,K2,L0
            else:
                d_outer = calculate_square_diameter (nturns, w, s, Ltarget, K1=K1_squarediff, K2=K2_squarediff, L0=L0_squarediff)  # technology specific, for generic technology remove parameters K1,K2,L0

            d_outer = math.ceil(d_outer*100)/100
            valid, do_min, _, _ = check_if_model_valid(nturns, w, s, d_outer, layout_with_centertap)

            # leave some reserve to shrink diameter, check against maximim diameter limit
            if (d_outer >= 1.1 * do_min) and (d_outer <= dout_max):            
                model_data_dict = {'nturns':nturns, 'w':w, 's':s, 'd_outer':d_outer} 
                geometry_candidates_list.append(model_data_dict)


# create GDSII and Palace model from list of geometry candidates
# If we have a centertap, draw that but don't simulate port 3 there for this initial sweep
palace_config_files, all_models_dict, data_dir, port_dict = create_models_from_list (geometry_candidates_list, layout_with_centertap, remove_centertap_for_EM=True)

# Give some feedback to user on the number of geometry candidates
wait_time_seconds = 10
print(f'\n\nThere are {len(geometry_candidates_list)} geometries that meet your specified parameters.\n')
print(f'Simulation will start in {wait_time_seconds} seconds.')
print(f'You can press Ctrl+C now to quit and review your specification, or wait for simulation starting in {wait_time_seconds} seconds.')
time.sleep(wait_time_seconds)

# Run all simulation models for initial sweep over parameter range
# Start measuring EM simulation 
start = time.perf_counter()
run_models_from_list (script_path, palace_config_files)
# evaluate simulation time
end = time.perf_counter()
log.append (f"INITIAL RESULTS (simulation time  {end - start:.1f} seconds):")


if len(palace_config_files) > 0:

    settings['order'] = finetune_FEM_order # switch to higher accuracy

    # get best results from initial sweep over all candidates
    best_list = get_best_results (palace_config_files, how_many_top_results, all_models_dict, port_dict)
 
    finetune_list = []
    for n in range(how_many_top_results):
      if len(best_list)>n:
        finetune_list.append(best_list[n]) 

    # now do finetune steps over the best candidates, that list is sorted by Q factor, top down
    for repeat in range(how_many_finetune_steps):
        palace_config_files, all_models_dict, data_dir, port_dict = create_models_from_list (finetune_list, layout_with_centertap, remove_centertap_for_EM=True)
        if len(palace_config_files)>0:
            start = time.perf_counter()
            run_models_from_list (script_path, palace_config_files)
            end = time.perf_counter()
            log.append(f'Finetune step {repeat+1} results sorted by Q factor (simulation time  {end - start:.1f} seconds):')
            finetune_list = get_best_results (palace_config_files, how_many_top_results, all_models_dict, port_dict)

    # Now we have done multiple finetune steps for multiple candidates, get the best one
    print('Now we have done multiple finetune steps for multiple candidates, get the best one')

    settings['fstart']  = 0
    settings['fstop']   = 2*ftarget
    settings['fstep']   = ftarget/40
    settings['fpoint']  = [ftarget]

    if len(finetune_list)>0:

        geometry_data = [finetune_list[0]]
        # now run wideband sweep on final result
        log.append(f'Running final wideband sweep for {geometry_data}')

        palace_config_files, all_models_dict, data_dir, port_dict = create_models_from_list (geometry_data, layout_with_centertap, remove_centertap_for_EM=True)
        start = time.perf_counter()
        run_models_from_list (script_path, palace_config_files)
        end = time.perf_counter()
        
        nturns = geometry_data[0]['nturns']
        w = geometry_data[0]['w']
        s = geometry_data[0]['s']
        d_outer = geometry_data[0]['d_outer']
        geometry_name = f"indSym_{ind_geom}_N{nturns}_do{d_outer}_w{w}_s{s}"

        log.append(f'Finished running wideband sweep for {geometry_name} (simulation time  {end - start:.1f} seconds)\n')

        # evaluate results again, because we might have used other simulation settings now
        if port_dict is not None:
            num_ports = len(port_dict)
            snp_file = f"{geometry_name}.s{num_ports}p"
            network = rf.Network(snp_file)
            freq, Rdiff, Ldiff, Qdiff = get_diff_model(network)
            # get data at target frequency
            ftarget_index = rf.find_nearest_index(freq, ftarget)
            L_at_ftarget = Ldiff[ftarget_index]
            Q_at_ftarget = Qdiff[ftarget_index]
            log.append(f"FINAL RESULT:\n  {network.name}: L={L_at_ftarget*1e9:.2f}nH Q={Q_at_ftarget:.1f}")
            log.append(f"  number of turns: {nturns}")
            log.append(f"  width: {w:.2f}")
            log.append(f"  spacing: {s:.2f}")
            log.append(f"  outer diameter: {d_outer:.2f}")
            log.append(f"  inner diameter: {d_outer-2*(nturns*w+(nturns-1)*s):.2f}")
            
            # Copy GDSII and SnP with prefix "final", so that we can identify the result more easily
            gds_filename = geometry_name + '.gds'
            final_gds_filename = 'final_' + gds_filename
            shutil.copy(gds_filename, final_gds_filename)
            log.append(f"GDSII file copied to {final_gds_filename}")

            final_snp_filename = 'final_' + snp_file
            shutil.copy(snp_file, final_snp_filename)
            log.append(f"S-parameter file copied to {final_snp_filename}")


            print('===============================================================================')
            for line in log:
                print(line)      

            # Do the plotting for differential parameters
            fig, axes = plt.subplots(1, 2, figsize=(12,6))  # NxN grid
            fig.suptitle("Differential Inductor Parameters")        

            # Inductance
            ax = axes[0]
            ax.set_ylim (0, 2*L_at_ftarget*1e9)
            ax.plot(freq / 1e9, Ldiff*1e9, label=network.name)
            ax.plot(ftarget/1e9, L_at_ftarget*1e9, 'ro', label = f"L={L_at_ftarget*1e9:.2f}nH @ {ftarget/1e9} GHz")
            ax.set_xlabel("Frequency (GHz)")
            ax.set_ylabel("Diff. Inductance (nH)")
            ax.set_xmargin(0)
            ax.legend(loc='lower left')
            ax.grid()

            # Q factor
            ax = axes[1]
            ax.set_ylim (0, 1.2*Q_at_ftarget)
            ax.plot(freq/1e9, Qdiff,label=network.name)
            ax.plot(ftarget/1e9, Q_at_ftarget,'ro', label = f"Q={Q_at_ftarget:.1f} @ {ftarget/1e9} GHz")
            ax.set_xlabel("Frequency (GHz)")
            ax.set_ylabel("Diff. Q factor")
            ax.set_xmargin(0)
            ax.legend(loc='lower left')
            ax.grid()

            plt.tight_layout()
            plt.show()

        else:
            log.append(f"FINAL RESULT:\n  Could not find geometries that match requirements (check number of turns)")        
            
            print('===============================================================================')
            for line in log:
                print(line)                         

    else:
        log.append("NO DATA: No results from initial sweep, no candidates for fine tune step, abort. One reason can be that simulation did not run.")        
  
        
        print('===============================================================================')
        for line in log:
            print(line)                        


else:
    # no results at all
    print('There are no inductor geometries that match your target value and parameter range!')
    exit(1)
