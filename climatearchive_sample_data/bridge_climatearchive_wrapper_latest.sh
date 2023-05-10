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
inputDir="/home/bridge/wb19586/ummodel/data"
netcdfDir="/home/bridge/wb19586/climatearchive/database/netcdf/BRIDGE"
pngDir="/home/bridge/wb19586/climatearchive/database/static/modelData/BRIDGE"

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

# experimentList="tEyee tEyed tEyec"

variableList="pr sic tos currents pfts winds"
#variableList="currents"

if [ -d ${scriptDir}/tmp ]; then rm -r ${scriptDir}/tmp; fi
mkdir ${scriptDir}/tmp
  
for experiment in ${experimentList}; do

  if [ -d ${netcdfDir}/${experiment} ]; then rm -r ${netcdfDir}/${experiment}; fi
  if [ -d ${pngDir}/${experiment} ]; then rm -r ${pngDir}/${experiment}; fi
  
  if [ -d ${inputDir}/${experiment}/${climate} ]; then
  
    echo "copying data for model: "${experiment}
    
    mkdir -p ${netcdfDir}/${experiment}/
    mkdir -p ${pngDir}/${experiment}/
  
    for variable in ${variableList}; do      

      # PD variables
      if [[ "${variable}" == "tas" ]]; then
        variableBRIDGE="temp_mm_1_5m"
        fileBRIDGE=a.pd
      elif [[ "${variable}" == "pr" ]]; then
        variableBRIDGE="precip_mm_srf"
        fileBRIDGE=a.pd
      elif [[ "${variable}" == "clt" ]]; then
        variableBRIDGE="totCloud_mm_ua"
        fileBRIDGE=a.pd

      # PC variables
      elif [[ "${variable}" == "winds" ]]; then
        variableBRIDGE="u_mm_p"
        fileBRIDGE=a.pc
        
      # PT variables
      elif [[ "${variable}" == "snc" ]]; then
        variableBRIDGE="snowCover_mm_srf"
        fileBRIDGE=a.pt
      elif [[ "${variable}" == "liconc" ]]; then
        variableBRIDGE="fracPFTs_mm_srf"
        fileBRIDGE=a.pt
      elif [[ "${variable}" == "pfts" ]]; then
        variableBRIDGE="fracPFTs_mm_srf"
        fileBRIDGE=a.pt        
      # PF variables
      elif [[ "${variable}" == "tos" ]]; then
        variableBRIDGE="temp_mm_uo"
        fileBRIDGE=o.pf
      elif [[ "${variable}" == "mlotst" ]]; then
        variableBRIDGE="mixLyrDpth_mm_uo"
        fileBRIDGE=o.pf
      elif [[ "${variable}" == "sic" ]]; then
        variableBRIDGE="iceconc_mm_uo"
        fileBRIDGE=o.pf
      elif [[ "${variable}" == "currents" ]]; then
        variableBRIDGE="ucurrTot_ym_dpth"
        fileBRIDGE=o.pg
      fi    
           
      # merge monthly mean files to climatology
      if [ ! -f ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.nc ] && [ "${variable}" != "currents" ] && [ "${variable}" != "winds" ]; then
        monthList="jan feb mar apr may jun jul aug sep oct nov dec"
        fileList=()
        
        for month in ${monthList}; do
          ncatted -a valid_min,,d,, -a valid_max,,d,, ${inputDir}/${experiment}/climate/${experiment}${fileBRIDGE}cl${month}.nc ${scriptDir}/tmp/${experiment}${fileBRIDGE}cl${month}.tmp.nc
          fileList+=(${scriptDir}/tmp/${experiment}${fileBRIDGE}cl${month}.tmp.nc) 
        done
        
        cdo cat ${fileList[@]} ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.nc       
      fi
      
      # mask ocean data
      if [ "${fileBRIDGE}" == "o.pf" ]; then
      
        # process variables on T-grid
        mv ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.nc ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.old.nc
        cdo -r ifnotthen -selvar,lsm ${inputDir}/${experiment}/inidata/${experiment}.qrparm.omask.nc ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.old.nc ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.masked.nc
        cdo -r setmisstonn ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.masked.nc ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.nc
        cdo sellonlatbox,-180,180,90,-90 ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.masked.nc ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.masked.shifted.nc

      fi
      

      if [  "${variable}" == "currents" ]; then    
        
        # process annual mean ocean velocities
#        cdo -r -setmisstoc,0 -remapnn,${inputDir}/${experiment}/inidata/${experiment}.qrparm.omask.nc ${inputDir}/${experiment}/climate/${experiment}${fileBRIDGE}clann.nc ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.remapnn.nc
        cdo -r -setmisstoc,0 ${inputDir}/${experiment}/climate/${experiment}${fileBRIDGE}clann.nc ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.remapnn.nc
        cdo sellonlatbox,-180,180,90,-90 ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.remapnn.nc ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.remapnn.shifted.nc
        cdo sellonlatbox,-180,180,90,-90 -setmisstoc,0  -intlevel,10.0,15.0,25.0,35.1,47.8,67.0,95.8,138.9,203.7,301.0,447.0,666.3,995.5,1500.8,2116.1,2731.4,3346.8,3962.1,4577.4,5192.6 -selvar,W_ym_dpth ${inputDir}/${experiment}/climate/${experiment}${fileBRIDGE}clann.nc ${scriptDir}/tmp/${experiment}${fileBRIDGE}.W.clim.masked.shifted.nc

      elif [  "${variable}" == "winds" ]; then    
        
        # process annual mean ocean velocities
        cdo sellonlatbox,-180,180,90,-90 ${inputDir}/${experiment}/climate/${experiment}${fileBRIDGE}clann.nc ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.shifted.nc

      else
  
        # select land ice from PFT data
        if [ "${variable}" == "liconc" ]; then
          mv ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.nc ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.old.nc
          cdo -r -sellevel,9 ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.old.nc ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.nc
        fi

        #extract monthly mean netcdf file for back-end access 
        cdo selvar,${variableBRIDGE} ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.nc ${netcdfDir}/${experiment}/${experiment}.${variable}.mm.nc
      
        tmpNetcdf=${scriptDir}/tmp/${experiment}.${variable}.clim.tmp.nc
      
        #shift longitudes to [-180,180] range
        cdo sellonlatbox,-180,180,90,-90 ${netcdfDir}/${experiment}/${experiment}.${variable}.mm.nc ${tmpNetcdf}      
      
      fi
      
      # create annual mean png file for THREE.js front-end access
      if [[ "${variable}" == "currents" ]]; then
        python ${scriptDir}/bridge_netcdf2png_currents.py --uvFile ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.remapnn.shifted.nc --variableBRIDGE ${variableBRIDGE} --wFile ${scriptDir}/tmp/${experiment}${fileBRIDGE}.W.clim.masked.shifted.nc  --variableOUT ${variable} --experiment ${experiment} --outputDir ${pngDir}/${experiment}/
      elif [[ "${variable}" == "winds" ]]; then
        python ${scriptDir}/bridge_netcdf2png_winds.py --uvFile ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.shifted.nc --variableBRIDGE ${variableBRIDGE} --variableOUT ${variable} --experiment ${experiment} --outputDir ${pngDir}/${experiment}/
      elif [[ "${fileBRIDGE}" == "o.pf" ]]; then
        python ${scriptDir}/bridge_netcdf2png_ocean.py --inputFile ${tmpNetcdf} --variableBRIDGE ${variableBRIDGE} --maskedFile ${scriptDir}/tmp/${experiment}${fileBRIDGE}.clim.masked.shifted.nc  --variableOUT ${variable} --experiment ${experiment} --outputDir ${pngDir}/${experiment}/
      elif [[ "${variable}" == "pfts" ]]; then
        python ${scriptDir}/bridge_netcdf2png_pfts.py --inputFile ${tmpNetcdf} --variableBRIDGE ${variableBRIDGE} --variableOUT ${variable} --experiment ${experiment} --outputDir ${pngDir}/${experiment}/
      else
        python ${scriptDir}/bridge_netcdf2png.py --inputFile ${tmpNetcdf} --variableBRIDGE ${variableBRIDGE} --variableOUT ${variable} --experiment ${experiment} --outputDir ${pngDir}/${experiment}/
      fi
      exit_status=$?
      rm -f ${tmpNetcdf}
      rm -f ${netcdfDir}/${experiment}/${experiment}.${variable}.mm.nc
      
    done
    
    # process boundary conditions
    
    # model height (combined bathymetry and orography on same grid)
  cdo -sellonlatbox,-180,180,90,-90 -selvar,ht ${inputDir}/${experiment}/inidata/${experiment}.qrparm.orog.nc ${scriptDir}/tmp/${experiment}.orog.nc
  cdo -sellonlatbox,-180,180,90,-90 -invertlat -setmisstoc,0 -mulc,-1 -selvar,depthdepth ${inputDir}/${experiment}/inidata/${experiment}.qrparm.omask.nc ${scriptDir}/tmp/${experiment}.bathy.nc
  cdo -add ${scriptDir}/tmp/${experiment}.orog.nc ${scriptDir}/tmp/${experiment}.bathy.nc ${scriptDir}/tmp/${experiment}.height.nc
   
   #create png file for THREE.js front-end access
  python ${scriptDir}/bridge_netcdf2png_height.py --inputFile ${scriptDir}/tmp/${experiment}.height.nc --variableBRIDGE ht --variableOUT "height" --experiment ${experiment} --outputDir ${pngDir}/${experiment}/

  fi  
  
  rm -r ${scriptDir}/tmp/${experiment}*
  
done

