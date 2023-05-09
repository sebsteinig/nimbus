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
    shape : Shape
    mode : Mode
    reshaped : np.ndarray
    output : np.ndarray
    output_mean : np.ndarray

    def __init__(self) -> None:
        self.z_5_dim = np.zeros((12, 12, 12, 12, 12))
        self.z_4_dim = np.zeros((12, 12, 12, 12))
        self.z_3_dim = np.zeros((12, 12, 12))
        self.z_2_dim = np.zeros((12, 12))
        self.z_1_dim = np.zeros((12))
        self.input_1 = [self.z_4_dim]
        self.input_2 = [self.z_4_dim, self.z_4_dim]
        
        arr = [np.zeros((3, 100)), np.zeros((3, 100)), np.zeros((3, 100))]
        #arr[0, 0, :] = 1
        #arr[1, 1, :] = 1
        #arr[2, 2, :] = 1
        self.input_3 = arr
        self.mode = get_mode(self.input_3)
        self.reshaped, self.shape = reshape_input(self.input_3)
        self.output = np.zeros((self.shape.lat, self.shape.lon * self.shape.time, self.mode.value))
        self.output_mean = np.zeros((self.shape.lat, self.shape.lon, self.mode.value))
        
        self.input_4 = [self.z_4_dim, self.z_4_dim, self.z_4_dim, self.z_4_dim]
        self.input_5 = [self.z_4_dim, self.z_4_dim, self.z_4_dim, self.z_4_dim, self.z_4_dim]