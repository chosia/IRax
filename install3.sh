#!/bin/bash
python3 -m pip install . --upgrade
python3 -m rax_kernel.install
NOTEBOOKPATH=`python3 -m pip show notebook | grep Location | cut -f 2 -d " "` 
NOTEBOOKPATH="${NOTEBOOKPATH}/notebook/static/components/codemirror/mode/rax"
if [ ! -d ${NOTEBOOKPATH} ]; then
  mkdir ${NOTEBOOKPATH}
fi
echo "Installing codemirror mode for Rax"
cp codemirror-rax/rax.js ${NOTEBOOKPATH}/
