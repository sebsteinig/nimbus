### nimbus

# Description
This program is a data converter that allows you to preprocess data from netCDF4 files and convert them into images for 3D visualization on https://climatearchive.org. It offers a wide range of options and features to customize the data conversion process to the user's needs. The program supports conversion of files (or folders of files) provided by the user.
## Usage:
```console
python nimbus.py [OPTIONS]
```
Options:
* --variables, -v: Select one or more variables (coma separated values) for conversion, 'all' for every variable specified in the configuration file. [See more](#configuration)
* --config, -c: Select configuration files. [See more](#configuration)
* --experiments, -e: Select one or more experiments id (coma separated values) for conversion .
* --folder, -f: Convert the given file or folder.
* --output, -o: Select file or folder.
* --clean, -cl: Clean the output directory.
* --debug, -d: Show debugs in the console.
* --chunkstime, -ct: specify the number of chunks (horizontally).
* --chunksvertical, -cv: specify the number of chunks (vertically).
* --labels, -l: specify labels for the given experiments for later use in the climate archive api.
* --publication, -p: only used with the climate archive api, specify a folder, a file or a url that contains information about published papers for more precise filtering of experiments in the climate archive api.

Usage Examples:
1. To select an experiment for conversion:
```console
    python nimbus.py -v variable1 -e expid -c config.toml
```
2. Send publication information to the database:
```console
    python nimbus.py -p file.html
```


# Configuration

To convert netCDF files, one must define the variables that are in these files. Many variables are already defined in the [Bridge configuration file](configs/BRIDGE_monthly.toml).
The configuration file can be written as follows, using the TOML language. Here is a simple example :
```console
    [Model]
    dir="your/directory/containig/data"
    name="your_name"
    [variable1]
    preprocessing="PREPROCESS_REF"
    processing="PROCESS_REF"
    files=["file1.nc", "file2.nc"]
    variable = "variable_name_in_netcdf_file"
    [Model.metadata]
    file = "file/containing/experiment/metadata"
    parser="type of parser for the file [bridge, dat, json]"
    tags = ["key of metadata that you want to store"]
    *any additional key value pair will be considered as default metadata tags
```

The preprocessing and processing attributes allows to reference the processing steps that should be applied to the data before conversion. ([See More](https://github.com/WillemNicolas/internship-climate-archive/edit/main/README.md#add-new-variables)). Here is a list of specification that can be added in the Model section of the configuration file :
1. specific levels, for example :

```console
      [Model.Atmosphere]
        levels = [1000, 850, 700, 500, 200, 100, 10]
        unit = "hPa"
        resolutions = [["default", "default"], [3.5, -5]]
```
Here we specify the list of levels that we are interested to display in the output images, the unit of these levels, and the resolutions. The resolutions are a list of lists where each list contains new values for longitude and latitude spacing in degrees. For each couple of values, an image will be produced with the desired resolution. If no resolutions are specified, or if the couple ```["default", "default"]``` is in the list, there will be no resizing of the input data.

2. resolutions, as a list of tuples where each tuple contains new values for longitude and latitude spacing in degrees. For example:
```console
    resolutions = [(3.5, -5)]
```

# Add New Variables
In order to add a new variable, one must define a new python file in the folder [supported_variables](supported_variables). The preprocessing and processing functions can be defined in this file, as well as the realm that corresponds to the variable. For example the variable [currents](supported_variables/currents.py) has a specific preprocessing function that we annotate with :
```console
    @preprocessing(currents,'BRIDGE')
```
And the argument 'BRIDGE' corresponds to the value assigned to 'preprocessing' in the TOML configuration file ([See BRIDGE_monthly.toml](configs/BRIDGE_monthly.toml)).

# Output
This program outputs images in the png folder, the output of the processed netCDF files given in input in the netcdf folder, and a log folder.  These 3 folders are in a folder named as the expID.  
The images are named as follows :    
```{configNAME}.{expID}.{variableNAME}.avg.png``` for the time mean image, and    
```{configNAME}.{expID}.{variableNAME}.ts.png``` for the time serie image.   
If resolutions are specified in the config file (and different than "default"), the resolutions will be specified in the image name :   
```{configNAME}.{expID}.{variableNAME}.rx{xVALUE}.ry{yVALUE}.[avg¦ts].png```

# Add New Variables
In order to add a new variable, one must define a new python file in the folder [supported_variables](supported_variables). The preprocessing and processing functions can be defined in this file, as well as the realm that corresponds to the variable. For example the variable [oceanCurrents](supported_variables/oceanCurrents.py) has a specific preprocessing function that we annotate with :
```console
    @preprocessing(OceanCurrents,'BRIDGE')
```
And the argument 'BRIDGE' corresponds to the value assigned to 'preprocessing' in the TOML configuration file ([See BRIDGE_monthly.toml](configs/BRIDGE_monthly.toml)).
# bridge-variable
1. clt :\
    named "totCloud_mm_ua" in bridge netcdf files

2. tas :\
    named "temp_mm_1_5m" in bridge netcdf files

3. pr :\
    named "precip_mm_srf" in bridge netcdf files

4. winds :\
    named "u_mm_p" in bridge netcdf files

5. snc :\
    named "snowCover_mm_srf" in bridge netcdf files

6. liconc :\
    named "fracPFTs_mm_srf" in bridge netcdf files

7. pfts :\
    named "fracPFTs_mm_srf" in bridge netcdf files

8. tos :\
    named "temp_mm_uo" in bridge netcdf files

9. mlotst :\
    named "mixLyrDpth_mm_uo" in bridge netcdf files

10. siconc :\
    named "iceconc_mm_uo" in bridge netcdf files

11. oceanCurrents :\
    named "ucurrTot_ym_dpth" in bridge netcdf files

12. height :\
    converted with inidata files --> qrparm.orog
