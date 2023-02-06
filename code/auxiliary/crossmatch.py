import pandas as pd
import numpy  as np
import os
from auxiliary.paths import input_path, raw_path
from astropy.table import Table
from auxiliary.columns import create_colors, calculate_colors
from auxiliary.columns import wise, galex, splus, error_splus
from auxiliary.correct_extinction import correction

def match_stilts(filename):
    input_filename = filename
    file = filename.split(os.path.sep)[-1]
    # input_filename = os.path.join(raw_path,filename)
    # input_filename = input_filename.replace(" ", "\ ")

    galex_filename = os.path.join(input_path, file.split('.')[0]+"_temp.fits")
    # galex_filename = filename.split('.')[0]+"_temp.fits"
    # galex_filename = galex_filename.replace(" ", "\ ")

    os.system(f"""java -jar stilts.jar cdsskymatch in={input_filename} cdstable=II/335/galex_ais ra=RA dec=DEC radius=2 find=each blocksize=100000 \\
                ocmd='addcol ID_GALEX "objid"; addcol sep_GALEX "angDist"; delcols "objid angDist"' out={galex_filename}""")

    output_filename = os.path.join(input_path,file)

    # output_filename = output_filename.replace(" ", "\ ")
    os.system(f"""java -jar stilts.jar cdsskymatch in={galex_filename} cdstable=II/363/unwise ra=RA dec=DEC radius=2 find=each blocksize=100000 \\
                ocmd='addcol ID_unWISE "objID"; addcol sep_unWISE "angDist"; delcols "objID angDist"' out={output_filename}""")
    os.system(f"""rm {galex_filename}""")

    return

def process_data(filename, correct_ext=True, save=False):
    pos_splus = ["ID", "RA", "DEC"]
    table = Table.read(filename)
    table = table.to_pandas()
    table["ID"] = table["ID"].str.decode('utf-8') 
    
    table['W1_MAG'] = 22.5 - 2.5*np.log10(table['FW1']) # + 2.699
    table['W2_MAG'] = 22.5 - 2.5*np.log10(table['FW2']) # + 3.339

    # http://doxygen.lsst.codes/stack/doxygen/x_masterDoxyDoc/namespacelsst_1_1afw_1_1image.html#a0a023f269211d52086723788764d484e
    # return std::abs(fluxErr / (-0.4 * flux * std::log(10)));
    table['e_W1_MAG'] = abs(table['e_FW1'] / (-0.4*table['FW1']*np.log(10)))
    table['e_W2_MAG'] = abs(table['e_FW2'] / (-0.4*table['FW2']*np.log(10)))

    table['W1_MAG'].replace([np.inf, -np.inf], np.nan, inplace=True)
    table['W2_MAG'].replace([np.inf, -np.inf], np.nan, inplace=True)

    table[wise+galex] = table[wise+galex].fillna(value=99)
    table.dropna(subset=splus, inplace=True)
    # table[wise] = table[wise].replace(-1, val_mb)

    if correct_ext:
        table = correction(table)
        save_filename = filename.split(os.path.sep)[-1].split('_')[0]+"_QSOs_VAC_ext.csv"
    else:
        save_filename = filename.split(os.path.sep)[-1].split('_')[0]+"_QSOs_VAC.csv"

    table = calculate_colors(table, broad=True, narrow=True, wise=True, galex = True, aper="PStotal")
    features = create_colors(broad=True, narrow=True, wise=True, galex=True, aper="PStotal")
    
    if save:
        table[pos_splus+features+splus+wise+galex+error_splus].to_csv(os.path.join(input_path, save_filename), index=False)

    return table[features]