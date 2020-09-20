def pre_mutation(context):
    if context.filename == "src/dso_tools/opcodes.py":
        context.skip = True
