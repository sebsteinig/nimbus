import unittest
from utils.png_converter import *
from unit_tests.utils.mock_png_converter import MockPngConverter

class TestPngConverter(unittest.TestCase):
    data : MockPngConverter

    def setUp(self) -> None:
        self.data = MockPngConverter()
        
    def test_get_mode_incorrect_types_failure(self):
        with self.assertRaises(IncorrectInputTypes):
            PngConverter.get_mode([1, 2, 3])
    
    def test_get_mode_too_many_inputs_failure(self):
        with self.assertRaises(IncorrectInputSize):
             PngConverter.get_mode(self.data.input_5)
    
    def test_get_mode_empty_list_failure(self):
        with self.assertRaises(IncorrectInputSize):
             PngConverter.get_mode([])

    def test_get_mode_success(self):
        self.assertEqual( PngConverter.get_mode(self.data.input_1), Mode.L)
        self.assertEqual( PngConverter.get_mode(self.data.input_2), Mode.RGB)
        self.assertEqual( PngConverter.get_mode(self.data.input_3), Mode.RGB)
        self.assertEqual( PngConverter.get_mode(self.data.input_4), Mode.RGBA)

    def test_reshape_input_incorrect_input_failure(self) :
        with self.assertRaises(IncorrectInputDim):
             PngConverter.reshape_input([self.data.z_1_dim, self.data.z_2_dim])

    def test_reshape_input_incorrect_n_variables_failure(self) :
        with self.assertRaises(IncorrectNumberOfVariables):
             PngConverter.reshape_input([self.data.z_5_dim])
        with self.assertRaises(IncorrectNumberOfVariables):
             PngConverter.reshape_input([self.data.z_1_dim])

    def test_reshape_input_success(self):
        reshaped, level, time, latitude, longitude =  PngConverter.reshape_input(self.data.input_4)
        self.assertEqual(reshaped.shape, (4, 12, 12, 12, 12))
        self.assertEqual((level, time, latitude, longitude), (12, 12, 12, 12))
        
    def test_minmax_succes(self):
        self.assertEqual( PngConverter.minmax(self.data.z_2_dim, 0.9, Logger.console()), (0,0))
        
    def test_fill_output_success(self):
        for i in range(3):
            self.data.pngConverter.fill_output(i, 0.9, Logger.console())
        self.assertEqual(self.data.pngConverter.output.shape, (3, 100, 3))
        path = PngConverter.save(self.data.pngConverter.output, "test_fill_output", "unit_tests/utils", Metadata(), "RGB")
        self.assertTrue(os.path.exists(path))

    def test_save_failure(self):
        with self.assertRaises(FileNotFoundError):
            PngConverter.save(self.data.pngConverter.output, "test_fill_output", "directory/that/doesnt/exist", Metadata(), "RGB")
        