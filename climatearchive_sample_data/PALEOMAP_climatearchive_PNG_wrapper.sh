#!/usr/bin/env bash
#
###############################################################################
#
# Copy selected experiments and variables from BRIDGE as test data for the
# climate archive app. Data is saved as netcdf and PNG in the database directory
# structure.
#
###############################################################################
set -e

scriptDir="/home/bridge/wb19586/climatearchive"
# pngDir="/home/bridge/wb19586/climatearchive/database/static/modelData/BRIDGE"
pngDir="/home/bridge/wb19586/climatearchive/database/static/modelData/vewa"

newOutputExperiment="PALEOMAP_FosterCO2_scotese_02"

# scotese_02
experimentList="texqe	texqd	texqc	texqb	texqa	teXPz	teXPy	teXPx	teXPw	teXPv "
experimentList+="teXPu	teXPt	teXPs	teXPr	teXPq	teXPp	teXPo	teXPn	teXPm	teXPl "	
experimentList+="teXPk	teXPj	teXPi	teXPh	teXPg	teXPf	teXPe	teXPd	teXPc	teXPb "	
experimentList+="teXPa	teXpz	teXpy	teXpx	teXpw	teXpv	teXpu	teXpt	teXps	teXpr "	
experimentList+="teXpq	teXpp	teXpo	teXpn	teXpm	teXpl	teXpk	teXpj	teXpi	teXph "	
experimentList+="teXpg	teXpf	teXpe	teXpd	teXpc	teXpb	teXpa	texPz	texPy	texPx	 "
experimentList+="texPw2 texPv1 texPu1 texPt1 texPs1 texPr1 texPq1 texPp1 texPo1 texPn1 " 
experimentList+="texPm1 texPl1 texPk1 texPj1 texPi1 texPh2 texPg1 texPf1 texPe2 texPd2 " 
experimentList+="texPc2 texPb2 texPa2 texpz1 texpy1 texpx2 texpw2 texpv1 texpu1 texpt2 " 
experimentList+="texps2 texpr2 texpq texpp texpo1 texpn1 texpm1 texpl1 texpk2 texpj2 " 
experimentList+="texpi1 texph1 texpg1 texpf texpe texpd texpc texpb texpa1 " 

# variableList="pr sic tos height oceanSurfaceCurrents winds pfts1 pfts2"
#variableList="oceanSurfaceCurrents"
variableList="surfaceWinds"

# scotese_04
# experimentList="tEyee tEyed tEyec tEyeb tEyea teYEz teYEy teYEx teYEw teYEv "
# experimentList+="teYEu teYEt teYEs teYEr teYEq teYEp teYEo teYEn teYEm teYEl "	
# experimentList+="teYEk teYEj teYEi teYEh teYEg teYEf teYEe teYEd teYEc teYEb "	
# experimentList+="teYEa teYez teYey teYex teYew teYev teYeu teYet teYes teYer "	
# experimentList+="teYeq teYep teYeo teYen teYem teYel teYek teYej teYei teYeh "	
# experimentList+="teYeg teYef teYee teYed teYec teYeb teYea teyEz teyEy teyEx "
# experimentList+="teyEw  teyEv  teyEu  teyEt  teyEs  teyEr  teyEq  teyEp  teyEo  teyEn " 
# experimentList+="teyEm  teyEl  teyEk  teyEj  teyEi  teyEh  teyEg  teyEf  teyEe  teyEd " 
# experimentList+="teyEc teyEb  teyEa  teyez  teyey  teyex  teyew  teyev  teyeu  teyet " 
# experimentList+="teyes  teyer  teyeq teyep teyeo  teyen  teyem  teyel  teyek  teyej " 
# experimentList+="teyei  teyeh  teyeg  teyef teyee teyed teyec teyeb teyea " 

# experimentList="tEyee tEyed"

#variableList="tas pr clt snc sic liconc tos currents oceanSurfaceCurrents height"
#variableList="winds"


if [ -d ${pngDir}/${newOutputExperiment} ]; then rm -r ${pngDir}/${newOutputExperiment}; fi
mkdir ${pngDir}/${newOutputExperiment}

for variable in ${variableList}; do

  fileList=()

  for experiment in ${experimentList}; do

    fileList+=("${pngDir}/${experiment}/${experiment}_${variable}.ym.png")
    
  done
  
  # reverse file list
#   min=0
#   max=$(( ${#fileList[@]} -1 ))
# 
#   while [[ min -lt max ]]
#   do
#       # Swap current first and last elements
#       x="${fileList[$min]}"
#       fileList[$min]="${fileList[$max]}"
#       fileList[$max]="$x"
# 
#       # Move closer
#       (( min++, max-- ))
#   done


  # cat PNGs horizontally
  convert +append ${fileList[@]} ${pngDir}/${newOutputExperiment}/${newOutputExperiment}_${variable}.541-0Ma.png  

done

