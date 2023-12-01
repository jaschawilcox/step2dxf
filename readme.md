# Assembly STEP to DXF plate exporter (GPTv4)

## Key Motivation and Need
This tool facilitates the preparation of files for fabrication from sheet stock, such as for laser cutters, plasma cutters, and waterjet machines. It addresses the key challenge of the traditionally tedious and slow process of preparing fabrication files. Instead of the manual, time-consuming task of selecting and exporting faces in an assembly or generating 2D drawing sets, this tool allows for the direct import of a STEP file of the entire assembly. It automatically identifies and exports the 2D plate geometry, significantly streamlining the workflow for engineers and fabricators.


## Introduction
Fabricating from sheet stock often requires converting 3D CAD models into 2D DXF files, a process that can be slow and error-prone when done manually. Our Python program automates this by extracting and exporting specific faces from a 3D model that are identified as plate components. It's specifically intended to handle full assemblies, identifying the relevant plates directly from the STEP file and exporting them as DXF files. The PythonOCC library is utilized for efficient handling of 3D geometric data.



## Requirements
- Python 3: The program is written in Python and requires Python 3.
- PythonOCC: Handles CAD data, installable via Conda:

```bash
conda install -c conda-forge pythonocc-core
```

- ezdxf: A Python package to create and modify DXF drawings, used for exporting data to DXF format. Install it using pip:

```bash
pip install ezdxf
```

## Usage
1. **Setup:** Ensure all required libraries are installed.
2. **Command Line Arguments:**
 - `step_file`: Path to the STEP file. (required)
 - `-t` or `--thickness`: Thickness to find (optional, default is 6).
 ```bash
python main.py sample1.step -t 6
```
3. **Execution:** Run the program with the required arguments. It will identify faces matching your criteria and export them to DXF files.
4. **Results:** Check the output folder for the DXF files and images highlighting the selected faces in the 3D model.


## Example
- **Input:** An entire assembly in STEP format.



- **Output:** 
  - DXF files for each identified face contained in output_dxf/.
  - Images displaying the 3D model with and without highlighted faces that meet the specified criteria.

  ![Example Input Image](output_without_highlight.png)
  *Input 3D model output_without_highlight.png*

  ![Example Output Image](output_with_highlight.png)
  *Output faces highlighted output_without_highlight.png*

    ![Example DXF](example_dxf.png)
  *Typical DXF output*

## Current Limitations and Future Work
- File Formats: Currently, the program only supports STEP files. Future versions could include support for other CAD formats.
- Complex Geometry: Handling very complex or large models may result in performance issues.
- User Interface: Currently CLI-based; a GUI could enhance usability.

## Contributions and Feedback
- Contributions to the codebase are welcome. Please refer to the contributing guidelines for more details.
- For feedback or issues, please open an issue on the project's GitHub page.

## Acknowledgment
[`sample3.step` source](https://grabcad.com/library/310-aptilla-led-lamp-a-1)

This software, and README, were prepared almost entirely using serial prompts of GPTv4.

**Initial prompt used to generate this readme:**
```
generate a readme.md for this program that tells why it is useful and how to use it. cover the following key points
- requirements, including how to install pythonocc using conda
- introduction, talking about how exporting dxf files from a 3d cad program can be tedius and time consuming
- the current limitations and future work 
- a note telling that most of the readme was written by chatgpt

***program source***
```