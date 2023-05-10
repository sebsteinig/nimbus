import sys
import numpy as np
from netCDF4 import Dataset
import argparse
from argparse import RawDescriptionHelpFormatter
from PIL import Image
import codecs, json
from json import encoder

encoder.FLOAT_REPR = lambda o: format(o, ".1f")

parser = argparse.ArgumentParser(
    description="""bridge_netcdf2png.py

Read in a single variable 12-month climatology of climate model output and converts them to
PNG files to reduce file sizes for network transfer and for easy loading in THREE.js and 
passing to the GPU.

""",
    formatter_class=RawDescriptionHelpFormatter,
)
parser.add_argument(
    "--inputFile", dest="inputFile", help="Full path of input netCDF file"
)
parser.add_argument(
    "--variableBRIDGE",
    dest="variableBRIDGE",
    help="Variable name in BRIDGE files",
)
parser.add_argument(
    "--variableOUT",
    dest="variableOUT",
    help="Variable name following CMIP convention",
)
parser.add_argument(
    "--experiment", dest="experiment", help="Name of BRIDGE simulation"
)
parser.add_argument(
    "--reference_file",
    dest="reference_file",
    help="Name of reference simulation for anomalies",
)
parser.add_argument(
    "--outputDir",
    dest="outputDir",
    help="Output directory to store the PNG files",
)
args = parser.parse_args()

# ***************************************************************************************
# load data and dimensions
# ***************************************************************************************

print(args.variableBRIDGE)

fInput = Dataset(args.inputFile)
inputData = fInput.variables[args.variableBRIDGE][:]
# remove dimensions of length 1 from 2d files
inputData = np.squeeze(inputData)
inputDims = list(fInput.variables[args.variableBRIDGE].dimensions)
if "ht" in inputDims:
    inputDims.remove("ht")
if "surface" in inputDims:
    inputDims.remove("surface")
if "unspecified" in inputDims:
    inputDims.remove("unspecified")
if "pseudo_1" in inputDims:
    inputDims.remove("pseudo_1")

if args.variableOUT == "orog":
    if "t" in inputDims:
        inputDims.remove("t")

inputRank = len(inputDims)

# check expected dimension names are parsed correctly and load dimension variables
# expected: (level) x (time) x lat x lon with optional dimensions in brackets
latName = inputDims[inputRank - 2]
if latName == "lat" or latName == "latitude":
    inputLat = fInput.variables[latName][:]
else:
    print("ERROR: unexpected latitude dimension name. EXITING script!")
    sys.exit(1)

lonName = inputDims[inputRank - 1]
if lonName == "lon" or lonName == "longitude":
    inputLon = fInput.variables[lonName][:]
else:
    print("ERROR: unexpected longitude dimension name. EXITING script!")
    sys.exit(1)

if inputRank > 2:
    timeName = inputDims[inputRank - 3]
    if (
        timeName == "month"
        or timeName == "time"
        or timeName == "t"
        or timeName == "time_counter"
    ):
        inputTime = fInput.variables[timeName][:]
    else:
        print("for file: " + args.inputFile + ":")
        print("ERROR: unexpected time dimension name. EXITING script!")
        sys.exit(1)

# ***************************************************************************************
# check and correct latitudes and longitudes
# ***************************************************************************************


# function to check for strictly increasing latitude and longitude coordinates
def strictly_increasing(L):
    return all(x < y for x, y in zip(L, L[1:]))


# latitude coordinates should decrease from 90 to -90 for correct orientation of PNG.
# therefore, test with strictly_increasing and reverse latitudes if this is true
if strictly_increasing(inputLat):
    inputLat = np.flip(inputLat, 0)
    inputData = np.flip(inputData, inputRank - 2)

# longitude coordinates should increase and start at -180 -> [-180,180] for cyclic
# longitude in Pacific. The CDO processing 'sellonlatbox,-180,180,90,-90' should take care
# of this. Nevertheless, test if this did actually work:

if strictly_increasing(inputLon):
    if np.amax(inputLon) > 180:
        print("for file: " + args.inputFile + ":")
        print(
            "ERROR: longitudes seem to be outside [-180,180]. EXITING script!"
        )
        sys.exit(1)
else:
    print("for file: " + args.inputFile + ":")
    print(
        "ERROR: longitudes do not seem to be strictly increasing. EXITING script!"
    )
    sys.exit(1)

# ************************************************************************************
# write data to PNG files
# ***************************************************************************************


def norm(arr, norm_min, norm_max):
    arr_min = norm_min
    arr_max = norm_max
    return (arr - norm_min) / (norm_max - norm_min)


outputData_ym = np.zeros((len(inputLat), len(inputLon) * 1))
outputData_mm = np.zeros((len(inputLat), len(inputLon) * 12))

if args.variableOUT == "tas":
    inputData = inputData - 273.15
    lowerBound = -50.0
    upperBound = 50.0
elif args.variableOUT == "tas_anomaly":
    ref_file = Dataset(args.reference_file)
    ref_data = np.squeeze(ref_file.variables[args.variableBRIDGE][:])
    ref_data_zm = np.mean(ref_data, axis=1, keepdims=True)
    # calculate anomaly wrt to reference zonal mean (normally PI)
    inputData -= ref_data_zm
    lowerBound = -50.0
    upperBound = 50.0
elif args.variableOUT == "pr":
    inputData = inputData * 86400.0
    lowerBound = 0.0
    upperBound = 25.0
elif args.variableOUT == "clt":
    lowerBound = 0.0
    upperBound = 1.0
elif args.variableOUT == "snc":
    outputData_ym[:, :] = norm(inputData_ym, 0.0, 1.0) * 255
    outputData_mm[:, :] = norm(inputData_mm, 0.0, 1.0) * 255
elif args.variableOUT == "tos":
    outputData_ym[:, :] = norm(inputData_ym, -2.0, 42.0) * 255
    outputData_mm[:, :] = norm(inputData_mm, -2.0, 42.0) * 255
elif args.variableOUT == "mlotst":
    outputData_ym[:, :] = norm(inputData_ym, 0.0, 1000.0) * 255
    outputData_mm[:, :] = norm(inputData_mm, -2.0, 1000.0) * 255
elif args.variableOUT == "sic":
    outputData_ym[:, :] = norm(inputData_ym, 0.0, 1.0) * 255
    outputData_mm[:, :] = norm(inputData_mm, 0.0, 1.0) * 255
elif args.variableOUT == "liconc":
    outputData_ym[:, :] = norm(inputData_ym, 0.0, 1.0) * 255
    outputData_mm[:, :] = norm(inputData_mm, 0.0, 1.0) * 255
elif args.variableOUT == "height":
    outputData_ym[:, :] = norm(inputData_ym, -5000.0, 5000.0) * 255
#   outputData_ym[:,:]   = norm(inputData_ym, -10000., 10000.) * 65535
elif args.variableOUT == "bathy":
    outputData_ym[:, :] = norm(inputData_ym, -5000.0, 0.0) * 255
elif args.variableOUT == "orog":
    outputData_ym[:, :] = norm(inputData_ym, 0.0, 5000.0) * 255

# monthly mean data
if inputRank > 2:
    inputData_ym = np.nanmean(inputData, axis=inputRank - 3)
    outputData_ym = norm(inputData_ym, lowerBound, upperBound) * 255

    for index in range(12):
        outputData_mm[
            :, index * len(inputLon) : ((index + 1) * len(inputLon))
        ] = (norm(inputData[index, :, :], lowerBound, upperBound) * 255)

# cap data to chosen dynamic range
outputData_ym[outputData_ym > 255] = 255
outputData_ym[outputData_ym < 0] = 0


# 8-bit PNG
img_ym = Image.fromarray(np.uint8(outputData_ym), "L")
img_ym.save(
    args.outputDir + args.experiment + "_" + args.variableOUT + ".ym.png"
)

if inputRank > 2:
    #   indMissingValues_mm = np.isnan(outputData_mm)
    #   outputData_mm = np.where(indMissingValues_mm, 255, outputData_mm)
    outputData_mm[outputData_mm > 255] = 255
    outputData_mm[outputData_mm < 0] = 0
    #   outputData_mm = np.where(indMissingValues_mm, 255, outputData_mm)

    img_mm = Image.fromarray(np.uint8(outputData_mm), "L")
    img_mm.save(
        args.outputDir + args.experiment + "_" + args.variableOUT + ".mm.png"
    )
