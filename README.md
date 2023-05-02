### internship-climate-archive

# Description:
This program is a data converter that allows you to preprocess data from netCDF4 files and convert them into images for 3D visualization on https://climatearchive.org. It offers a wide range of options and features to customize the data conversion process to the user's needs. The program supports conversion of files (or folders of files) provided by the user.

Usage:
python nc_to_img.py [OPTIONS]

Options:
* --variables, -v: Select variables for conversion, 'all' for every variable specified in the configuration file. [See more](#configuration)
* --config, -c : Select configuration files. [See more](#configuration)
* --experiences, -e: Select experience id for conversion .
* --files, -f: Convert the given file or folder.
* --output, -o: Select file or folder.
* --clean, -cl: Clean the output directory.
Usage Examples:
1. To select variables for conversion in one file :
```console
    python nc_to_img.py -v variable1,variable2,variable3 -f file.nc -c config.toml
```
2. To select all variables for conversion in one file:
```console
    python nc_to_img.py -v all -f file.nc -c config.toml
```
3. To select an experience for conversion:
```console
    python nc_to_img.py -v variable1 -e expid -c config.toml
```
4. To clean the output directory:
```console
    python nc_to_img.py -v variable1 -e expid -c config.toml -cl
```
5. To convert the given file or folder:
```console
    python nc_to_img.py -v variable1 -f folder -c config.toml 
```
# configuration
To convert netCDF files, one must define the variables that are in these files. Many variables are already defined in the [Bridge configuration file](BRIDGE.toml).
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
```
The preprocessing and processing attributes allows to reference the processing steps that should be applied to the data before conversion. ([See More](https://github.com/WillemNicolas/internship-climate-archive/edit/main/README.md#add-new-variables)). Here is a list of specification that can be added in the Model section of the configuration file :
1. specific levels, for example :
```console
      [Model.Atmosphere]
        levels = [1000, 850, 700, 500, 200, 100, 10]
        unit = "hPa"
```
2. resolutions, as a list of tuples where each tuple contains new values for longitude and latitude spacing in degrees. For example:
```console
    resolutions = [(3.5, -5)]
```
# Add New Variables
In order to add a new variable, one must define a new python file in the folder [supported_variables](supported_variables). The preprocessing and processing functions can be defined in this file, as well as the realm that corresponds to the variable. For example the variable [oceanCurrents](supported_variables/oceanCurrents.py) has a specific preprocessing function that we annotate with :
```console
    @preprocessing(OceanCurrents,'BRIDGE')
```
And the argument 'BRIDGE' corresponds to the value assigned to 'preprocessing' in the TOML configuration file ([See BRIDGE.toml](BRIDGE.toml)).
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
