import folder_paths

class GetComfyInputPath:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {}}

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("input_path",)
    FUNCTION = "get_path"
    CATEGORY = "Same Nodes/Utils"

    def get_path(self):
        return (folder_paths.get_input_directory(),)

NODE_CLASS_MAPPINGS = {
    "GetComfyInputPath": GetComfyInputPath
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "GetComfyInputPath": "Get ComfyUI Input Path"
}