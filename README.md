# HQCMeas: versatile data acquisition software for complex experiments.

<div>
<a href='https://travis-ci.org/MatthieuDartiailh/HQCMeas'><img src='https://travis-ci.org/MatthieuDartiailh/HQCMeas.svg?branch=master' alt='Build Status' /></a> 
<a href='https://coveralls.io/r/MatthieuDartiailh/HQCMeas'><img src='https://coveralls.io/repos/MatthieuDartiailh/HQCMeas/badge.png' alt='Coverage Status' /></a>
</div>

HQCMeas is a versatile and intuitive data acquisition software. Its 
hierarchical tree structure enables standard multiple loops programming 
but also sequential mutliple tasks needed for complex experiments. 
Building any program, including a simple multiple loop program, is 
intuitive and fast. It can be done at the topmost level, without going 
back to the code. You just need the drivers for the instruments. 
Provided these drivers are available, you can build a data acquisition 
sequence simply by using the scroll bars and dialog boxes appearing in 
the graphical interface. The dialog boxes allow you to enter values, 
timing and instructions for a given instrument. Each measurement 
template can be saved separately. When saving data  a header summarizing
for example the main fixed parameters of a given measurement can be added,
making data post processing very easy.

## Dependencies :

### Non optional
- Python 2.7
- enaml > 0.9.7
- configobj
- watchdog

### Optional
- pyvisa (for controlling instruments through the VISA protocol)
