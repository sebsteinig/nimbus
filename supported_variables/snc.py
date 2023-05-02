if __name__ == "__main__":
    from supported_variables.utils.supported_variable import supported_variable
    import utils.utils as utils
else :
    from supported_variables.utils.supported_variable import supported_variable

@supported_variable
class Snc:
    realm = 'a'
