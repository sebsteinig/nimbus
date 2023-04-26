### internship-climate-archive
Program Name: Data Converter

Description:
This program is a data converter that allows you to preprocess data from netCDF4 files and convert them into images for 3D visualization on https://climatearchive.org. It offers a wide range of options and features to customize the data conversion process to the user's needs. The program supports conversion of files or folders provided by the user or conversion of bridge data based on their experience id.

Usage:
python nc_to_img.py [OPTIONS]

Options:
--bridge_variables, -bv: Select bridge variables for conversion. [See more](#bridge-variable)
--new_variables, -nv: Create new variables with default preprocessing and processing.
--experiences, -e: Select experience id for conversion .
--all-bridge-variables, -av: Select all bridge variables for conversion.
--files, -f: Convert the given file or folder.
--bridge, -b: Convert the given file or folder from bridge.
--clean, -c: Clean the output directory.
--threshold, -t: Specify the threshold of maximum and minimum values (must be between 0 and 1, default is 0.95).
--resolutions, -r: Specify resolutions for image processing (must be between 0 and 1, where 1 means 100% resolutions of netcdf grid input, default is 1).

Usage Examples:
1. To select bridge variables for conversion:
```console
    python nc_to_img.py -bv variable1,variable2,variable3 -f file.nc
```
2. To create new variables with default preprocessing and processing:
```console
    python nc_to_img.py -nv variable1 -f file.nc
```
3. To select experience for conversion:
```console
    python nc_to_img.py -bv variable1 -b folder -e expid
```
4. To select all bridge variables for conversion:
```console
    python nc_to_img.py -av -b folder
```
5. To convert the given file or folder:
```console
    python nc_to_img.py -bv variable1 -f folder 
```
6. To convert the given file or folder from bridge:
```console
    python nc_to_img.py -bv variable1 -b folder
```
7. To clean the output directory:
```console
    python nc_to_img.py -bv variable1 -b folder -c
```
8. To specify threshold for maximum and minimum values:
```console
    python nc_to_img.py -bv variable1 -b folder -t 0.90
```
9. To specify resolutions for image processing:
```console
    python nc_to_img.py -bv variable1 -b folder -r 0.5,0.9
```
# bridge-variable
1. clt : 
    named "totCloud_mm_ua" in bridge netcdf files

2. tas : 
    named "temp_mm_1_5m" in bridge netcdf files

3. pr : 
    named "precip_mm_srf" in bridge netcdf files

4. winds : 
    named "u_mm_p" in bridge netcdf files

5. snc : 
    named "snowCover_mm_srf" in bridge netcdf files

6. liconc : 
    named "fracPFTs_mm_srf" in bridge netcdf files

7. pfts : 
    named "fracPFTs_mm_srf" in bridge netcdf files

8. tos : 
    named "temp_mm_uo" in bridge netcdf files

9. mlotst : 
    named "mixLyrDpth_mm_uo" in bridge netcdf files

10. siconc : 
    named "iceconc_mm_uo" in bridge netcdf files

11. oceanCurrents : 
    named "ucurrTot_ym_dpth" in bridge netcdf files

12. height : 
    converted with inidata files --> qrparm.orog