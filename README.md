# Dataset Curation Tool

A desktop image preselection and labeling application built with Python, Tkinter, and Pillow for efficient dataset curation and metadata preparation.

The tool is designed to simplify image review workflows by allowing users to browse folders, inspect images, assign scene-level attributes, and store selections in a structured CSV format.

---

## Overview

Preparing clean and well-structured datasets is an important step in computer vision and machine learning workflows.

This tool provides a simple desktop interface for reviewing large image collections and recording useful metadata during the preselection and curation process.

It supports image navigation, zooming and dragging, scene-based labeling, CSV logging, undo functionality, search, and light/dark themes.

---

## Features

- Desktop GUI for image review and labeling
- Folder-based image navigation
- Image zoom and drag support
- Scene-based attribute selection
- CSV-based metadata logging
- Search support for image folders
- Undo functionality
- Dark and light themes
- Overwrite confirmation for saved metadata
- Structured image preselection workflow
- Standalone desktop packaging using PyInstaller

---

## Workflow

```text
Image Dataset
     |
     v
Folder Selection
     |
     v
Image Review
     |
     v
Scene / Attribute Selection
     |
     v
Metadata Recording
     |
     v
CSV Output
     |
     v
Curated Dataset
```

---

## Use Case

The tool is useful during dataset preparation stages where a large number of images need to be manually inspected and filtered before annotation, training, or further processing.

Typical use cases include:

- image preselection
- scene categorization
- dataset cleanup
- metadata generation
- annotation preparation
- computer vision dataset curation

---

## Technologies

- Python
- Tkinter
- Pillow
- CSV
- Desktop GUI Development
- Dataset Curation
- Image Processing

---

## Repository Structure

```text
dataset-curation-tool/
├── PS-Tool/
│   └── application files
├── README.md
└── requirements.txt
```

Update this section later if the internal folder structure is reorganized.

---

## Installation

Clone the repository:

```bash
git clone https://github.com/RahulR666/PS-Tool.git
cd PS-Tool
```

Install the required dependencies:

```bash
pip install -r requirements.txt
```

---

## Running the Application

Run the main Python application file.

For example:

```bash
python GUI_tool.py
```

If the actual main file has a different name or is inside the `PS-Tool/` directory, update this command accordingly.

---

## How It Works

### 1. Select an Image Folder

Choose the folder containing the images that need to be reviewed.

### 2. Browse Images

Navigate through the images using the application controls.

Users can inspect images more closely using zoom and drag functionality.

### 3. Assign Scene Attributes

Select the relevant scene or metadata attributes for each image.

### 4. Save Metadata

The selected information is written to a structured CSV file for later use in dataset preparation or annotation workflows.

### 5. Correct Mistakes

Undo functionality allows recent actions to be reverted when required.

---

## Interface Features

### Image Viewer

Provides image display with zooming and dragging for detailed inspection.

### Folder Navigation

Allows navigation through image directories and supports search functionality.

### Metadata Selection

Provides controls for selecting image-level or scene-level attributes.

### Theme Support

Supports both dark and light interface modes.

### Data Safety

Overwrite confirmation helps prevent accidental replacement of existing metadata.

---

## Output

The tool stores the selected image information and metadata in CSV format.

A typical output structure may contain fields such as:

```text
image_name, attribute_1, attribute_2, attribute_3, ...
```

The exact columns depend on the configuration and labeling workflow used by the application.

---

## Demo

<!-- ADD APPLICATION SCREENSHOT HERE -->

Future additions can include:

- main application interface
- image review window
- metadata selection panel
- zoomed image example
- CSV output example

Example:

```markdown
![Dataset Curation Tool](results/application_interface.png)
```

---

## Packaging as a Desktop Application

The application can be packaged into a standalone executable using PyInstaller.

Install PyInstaller:

```bash
pip install pyinstaller
```

Create the executable:

```bash
pyinstaller --onefile GUI_tool.py
```

Depending on the application structure and GUI requirements, additional PyInstaller options may be required.

The generated executable will typically be available inside:

```text
dist/
```

---

## Future Improvements

Potential improvements include:

- configurable label categories
- keyboard shortcuts for faster annotation
- multi-image preview
- annotation statistics
- progress tracking
- dataset summaries
- additional export formats
- integration with annotation platforms
- batch operations
- automated image-quality checks

---

## Author

**Rahul Rathnam**

Robotics Software Engineer  
Localization | Perception | Sensor Fusion | Autonomous Systems

GitHub: [RahulR666](https://github.com/RahulR666)
