#!/bin/bash
pip install . --upgrade
python -m rax_kernel.install --prefix /opt/conda
NOTEBOOKPATH=`pip show notebook | grep Location | cut -f 2 -d " "` 
NOTEBOOKPATH="${NOTEBOOKPATH}/notebook/static/components/codemirror/mode/rax"
if [ ! -d ${NOTEBOOKPATH} ]; then
  mkdir ${NOTEBOOKPATH}
fi
echo "Installing codemirror mode for Rax"
cp codemirror-rax/rax.js ${NOTEBOOKPATH}/