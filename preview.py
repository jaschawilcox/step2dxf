from OCC.Display.SimpleGui import init_display
from OCC.Extend.DataExchange import read_step_file

def render_step_to_png(step_file, output_png):
    # Initialize the 3D display
    display, start_display, add_menu, add_function_to_menu = init_display()

    # Read the STEP file
    shape = read_step_file(step_file)

    # Display the shape
    display.DisplayShape(shape, update=True)

    # Set up an isometric view
    display.View_Iso()
    display.FitAll()

    # Save the rendering to a PNG file
    display.View.Dump(output_png)

# Usage
render_step_to_png("your_step_file.step", "output.png")