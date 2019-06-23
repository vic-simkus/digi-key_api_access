#===============================================================================
#
#  Copyright 2017 VIDAS SIMKUS
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#
#===============================================================================


SMT_KEYWORDS = ('SOT', 'SOIC', '1206', 'TQFP','DO-214AA',"SC-76","SOD-323","0805")

# These are values for the "Mounting Type" parameter; parameter ID 69
# 453 -- Surface mount, MLCC
# 3 -- Surface mount
DIGIKEY_SMT_MOUNTING_TYPES = (453,3)

DIGIKEY_TH_MOUNTING_TYPES = (80,367,123)

# 319 -- HC49/US
# 11811 -- Radial, can
# 2 -- Radial
# 10828  - TO-220
# 1 - Axial
# 6547 - 8-DIP
# 8459 - TO-251
# 13139 - TO-92
# 8250 - TO-220-3
# 7272 - SIP-3

DIGIKEY_TH_PACKAGE_TYPES = (319,11811,2,10828,1,6547,8459,13139,8250,7272)

PKG_TH_TO_220 = 10828
PKG_TH_HC_49 = 319
PKG_TH_DIP_8 = 6547
PKG_TH_TO_251 = 8459
PKG_TH_TO_92 = 13139

#===============================================================================
#
# DigiKey SMT package types.
#
#===============================================================================

# These are values for the "Package / Case" parameter; parameter ID 16
# 7 - 1206
# 6 - 0805
# 12624 - TO-236
# 333 - DO214
# 10180 - SC-76, SOD-323
# 6548 - 8-SOIC
# 6534 - 28-SOIC
# 11427 - 44-TQFP
# 5120 - 2512
# 6514	- 16-SOIC
# 12624 - SOT-23
# 6510 - SOIC-14
# 10109 - SOD-123F
# 10504 - TO-277
# 13421 - 16-SSOP
# 986 - SOT-23-6
# 160 - SOT-23-5
# 13125 - 10-MSOP
# 8582 - 14-TSSOP
# 15647 - 1206 WIDE


DIGIKEY_SMT_PACKAGE_TYPES = (6,7,12624,333,10180,6548,6534,11427,5120,6514,12624,6511,10109,10504,13421,986,160,13125,8582,15647)

PKG_DK_SMT_INVALID = -1
PKG_DK_SMT_1206 = 7
PKG_DK_SMT_0805 = 6
PKG_DK_SMT_2512 = 5120
PKG_DK_SMT_TO_236 = 12624
PKG_DK_SMT_DO_214 = 333
PKG_DK_SMT_SC_76 = 10180
PKG_DK_SMT_SOIC_8 = 6548
PKG_DK_SMT_SOIC_14 = 6511
PKG_DK_SMT_SOIC_16 = 6514
PKG_DK_SMT_SOIC_28 = 6534
PKG_DK_SMT_TQFP_44 = 11427
PKG_DK_SMT_SOT_23 = 12624
PKG_DK_SMT_SOD_123F = 10109
PKG_DK_SMT_TO_277 = 10504
PKG_DK_SMT_16_SSOP = 13421
PKG_DK_SMT_SOT_23_6 = 986
PKG_DK_SMT_SOT_23_5 = 160
PKG_DK_SMT_MSOP_10 = 13125
PKG_DK_SMT_TSSOP_14 = 8582
PKG_DK_SMT_1206_WIDE = 15647

def digikey_smt_type_to_string(_type):
	if _type == -1:
		return "INVALID"
	elif _type == 7:
		return "1206"
	elif _type == 6:
		return "0805"
	elif _type == 5120:
		return "2512"
	elif _type == 12624:
		return "TO_236"
	elif _type == 333:
		return "DO_214"
	elif _type == 10180:
		return "SC_76" 
	elif _type == 6548:
		return "SOIC_8"
	elif _type == 6511:
		return "SOIC_14"
	elif _type == 6514:
		return "SOIC_16"
	elif _type == 6534:
		return "SOIC_28"
	elif _type == 11427:
		return "TQFP_44"
	elif _type == 12624:
		return "SOT_23" 
	elif _type == 10109:
		return "SOD_123F" 
	elif _type == 10504:
		return "TO_277" 
	elif _type == 13421:
		return "SSOP_16" 
	elif _type == 986:
		return "SOT_23_6" 
	elif _type == 160:
		return "SOT_23_5" 
	elif _type == 13125:
		return "MSOP_10" 
	elif _type == 8582:
		return "TSSOP_14" 
	elif _type == 15647:
		return "1206_WIDE" 
	else:
		return "*ERR(%s)*" % str(_type)



#===============================================================================
#
# Broad pacakge mount types.  Either through hole (TH) or surface mount (SMT).
#
#===============================================================================

PKG_MOUNT_TYPE_UNKNOWN = 0
PKG_MOUNT_TYPE_AMBIG = 1
PKG_MOUNT_TYPE_TH = 2
PKG_MOUNT_TYPE_SMT = 3

def pkg_mount_type_to_string(_type):
	"""
	Converts the PKG_MOUNT_
TYPE_* contstants to a human readable string.
	"""
	if _type == 0:
		return "UNKNOWN"
	elif _type == 1:
		return "AMBIG"
	elif _type == 2:
		return "TH"
	elif _type == 3:
		return "SMT"
	else:
		return "*ERR(%s)*" % str(_type)



CASE_EQUIVALENT = (
		('SOT_23','TO_236','TO_236AB'),
		('SOT-23-6','SC-74',)
	)