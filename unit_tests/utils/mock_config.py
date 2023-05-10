
from utils.config import *

def build(name:str = "TEST_CONFIG"):
    desc = "TEST_CONFIG"
    
    config = {}
    config["Model"] = {
        "dir" : "mock_test_dir/",
        "name" : name,
        "Atmosphere" : {
            "levels" : [1000, 850, 700, 500, 200, 100, 10],
            "unit" :  [0, 100, 200, 500, 1000, 2000, 4000]
        },
        "Atmosphere" : {
            "levels" : [1000, 850, 700, 500, 200, 100, 10],
            "unit" :  [0, 100, 200, 500, 1000, 2000, 4000]
        },
        "threshold" : 0.90,
    }
    config["clt"] = {
        "variables" : [{
            "files" :"{regex}{id}/climate/{id}a.pdcl(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).nc",
            "variable" : "totCloud_mm_ua",
        }]
    }

    config["tas"] = {
        "variables" : [{
            "files" :"{regex}{id}/climate/{id}a.pdcl(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).nc",
            "variable" : "temp_mm_1_5m",
        }]
    }
    
    config["pr"] = {
        "variables" : [{
            "files":"{regex}{id}/climate/{id}a.pdcl(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).nc",
            "variable": "precip_mm_srf"
        }]
    }
    

    config["winds"] = {
        "variables" : [{
            "files":"{regex}{id}/climate/{id}a.pccl(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).nc",
            "variable": "u_mm_p"
        },
        {
            "files":"{regex}{id}/climate/{id}a.pccl(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).nc",
            "variable": "v_mm_p"
        }
        ]
    }
    

    config["snc"] = {
        "variables" : [{
            "files":[
                "{id}/climate/{id}a.ptcljan.nc",
                "{id}/climate/{id}a.ptclfeb.nc",
                "{id}/climate/{id}a.ptclmar.nc",
                "{id}/climate/{id}a.ptclapr.nc",
                "{id}/climate/{id}a.ptclmay.nc",
                "{id}/climate/{id}a.ptcljun.nc",
                "{id}/climate/{id}a.ptcljul.nc",
                "{id}/climate/{id}a.ptclaug.nc",
                "{id}/climate/{id}a.ptclsep.nc",
                "{id}/climate/{id}a.ptcloct.nc",
                "{id}/climate/{id}a.ptclnov.nc",
                "{id}/climate/{id}a.ptcldec.nc",
            ],
            "variable": "snowCover_mm_srf"
        }],
    }
    
    config["liconc"] = {
        "variables" : [{
            "files":"{regex}{id}/climate/{id}a.ptcl(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).nc",
            "variable": "fracPFTs_mm_srf"
        }]
    }
    
    config["pfts"] = {
        "variables" : [{
            "files":"{regex}{id}/climate/{id}a.ptcl(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).nc",
            "variable": "fracPFTs_mm_srf"
        }]
    }
    
    config["tos"] = {
        "variables" : [{
            "files":"{regex}{id}/climate/{id}o.pfcl(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).nc",
            "variable": "temp_mm_uo"
        },
        {
            "files":"{id}/inidata/{id}.qrparm.omask.nc",
            "variable": "lsm" 
        }
        ]
    }
    
   


    config["mlotst"] = {
        "variables" : [{
            "files":"{regex}{id}/climate/{id}o.pfcl(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec).nc",
            "variable": "mixLyrDpth_mm_uo"
        }]
    }
    
   
    config["sic"] = {
        "variables" : [{
            "files":[
                "{id}/climate/{id}o.pfcljan.nc",
                "{id}/climate/{id}o.pfclfeb.nc",
                "{id}/climate/{id}o.pfclmar.nc",
                "{id}/climate/{id}o.pfclapr.nc",
                "{id}/climate/{id}o.pfclmay.nc",
                "{id}/climate/{id}o.pfcljun.nc",
                "{id}/climate/{id}o.pfcljul.nc",
                "{id}/climate/{id}o.pfclaug.nc",
                "{id}/climate/{id}o.pfclsep.nc",
                "{id}/climate/{id}o.pfcloct.nc",
                "{id}/climate/{id}o.pfclnov.nc",
                "{id}/climate/{id}o.pfcldec.nc",
            ],
            "variable": "iceconc_mm_uo"
        },
        {
            "files":"{id}/inidata/{id}.qrparm.omask.nc",
            "variable": "lsm"
        }
        ]
    }
    
    config["currents"] = {
        "variables" : [{
            "files":"{id}/climate/{id}o.pgclann.nc",
            "variable": "ucurrTot_ym_dpth"
        },
        {
            "files":"{id}/climate/{id}o.pgclann.nc",
            "variable": "vcurrTot_ym_dpth"
        }
        ]
    }
    
    config["height"] = {
        "variables" : [{
            "files":"{id}/inidata/{id}.qrparm.orog.nc",
            "variable": "ht"
        },
        { 
            "files":"{id}/inidata/{id}.qrparm.omask.nc",
            "variable": "depthdepth"  
        }
        ]
    }
    
    return Config._build(config,desc)
    
    