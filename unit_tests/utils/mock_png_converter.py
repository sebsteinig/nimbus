from utils.png_converter import *

class MockPngConverter:
    z_5_dim : np.ndarray
    z_4_dim : np.ndarray
    z_3_dim : np.ndarray
    z_2_dim : np.ndarray
    z_1_dim : np.ndarray
    input_1 : list
    input_2 : list
    input_3 : list
    input_4 : list
    input_5 : list
    pngConverter : PngConverter

    def __init__(self) -> None:
        self.z_5_dim = np.zeros((12, 12, 12, 12, 12))
        self.z_4_dim = np.zeros((12, 12, 12, 12))
        self.z_3_dim = np.zeros((12, 12, 12))
        self.z_2_dim = np.zeros((12, 12))
        self.z_1_dim = np.zeros((12))
        self.input_1 = [self.z_4_dim]
        self.input_2 = [self.z_4_dim, self.z_4_dim]
        
        arr0 = np.zeros((3, 100))
        arr1 = np.zeros((3, 100))
        arr2 = np.zeros((3, 100))
        arr0[0, :] = 1
        arr1[1, :] = 1
        arr2[2, :] = 1
        self.input_3 = [arr0, arr1, arr2]
        self.pngConverter = PngConverter(self.input_3)
        
        self.input_4 = [self.z_4_dim, self.z_4_dim, self.z_4_dim, self.z_4_dim]
        self.input_5 = [self.z_4_dim, self.z_4_dim, self.z_4_dim, self.z_4_dim, self.z_4_dim]