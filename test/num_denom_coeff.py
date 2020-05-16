# https://github.com/SiggiGue/pyfilterbank 
import pyfilterbank


from pyfilterbank import splweighting, sosfiltering

b, a = splweighting.a_weighting_coeffs_design(48000)

