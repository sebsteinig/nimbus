### internship-climate-archive

# Description
This program is a data converter that allows you to preprocess data from netCDF4 files and convert them into images for 3D visualization on https://climatearchive.org. It offers a wide range of options and features to customize the data conversion process to the user's needs. The program supports conversion of files (or folders of files) provided by the user.

## Usage:
```console
python nc_to_img.py [OPTIONS]
```
Options:
* --variables, -v: Select variables for conversion, 'all' for every variable specified in the configuration file. [See more](#configuration)
* --config, -c : Select configuration files. [See more](#configuration)
* --experiences, -e: Select experience id for conversion .
* --files, -f: Convert the given file or folder.
* --output, -o: Select file or folder.
* --clean, -cl: Clean the output directory.
* 
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
# Configuration
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
The preprocessing and processing attributes allows to reference the processing steps that should be applied to the data before conversion. ([See More](https://github.com/WillemNicolas/internship-climate-archive/edit/main/README.md#add-new-variables)). In the ```[Model]``` section, you can add specififations for realms. Here is an example :
```console
      [Model.Atmosphere]
        levels = [1000, 850, 700, 500, 200, 100, 10]
        unit = "hPa"
        resolutions = [["default", "default"], [3.5, -5]]
```
Here we specify the list of levels that we are interested to display in the output images, the unit of these levels, and the resolutions. The resolutions are a list of lists where each list contains new values for longitude and latitude spacing in degrees. For each couple of values, an image will be produced with the desired resolution. If no resolutions are specified, or if the couple ```["default", "default"]``` is in the list, there will be no resizing of the input data.

# Add New Variables
In order to add a new variable, one must define a new python file in the folder [supported_variables](supported_variables). The preprocessing and processing functions can be defined in this file, as well as the realm that corresponds to the variable. For example the variable [oceanCurrents](supported_variables/oceanCurrents.py) has a specific preprocessing function that we annotate with :
```console
    @preprocessing(OceanCurrents,'BRIDGE')
```
And the argument 'BRIDGE' corresponds to the value assigned to 'preprocessing' in the TOML configuration file ([See BRIDGE.toml](BRIDGE.toml)).

# Output
This program outputs images in the png folder, the output of the processed netCDF files given in input in the netcdf folder, and a log folder.  These 3 folders are in a folder named as the expID.  
The images are named as follows :    
```{configNAME}.{expID}.{variableNAME}.avg.png``` for the time mean image, and    
```{configNAME}.{expID}.{variableNAME}.ts.png``` for the time serie image.   
If resolutions are specified in the config file (and different than "default"), the resolutions will be specified in the image name :   
```{configNAME}.{expID}.{variableNAME}.rx{xVALUE}.ry{yVALUE}.[avg¦ts].png```.
