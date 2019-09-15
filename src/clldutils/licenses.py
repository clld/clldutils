import pathlib

import attr

_LICENSES = {
    "Glide": {
        "name": "3dfx Glide License",
        "url": "http://www.users.on.net/~triforce/glidexp/COPYING.txt",
    },
    "Abstyles": {
        "name": "Abstyles License",
        "url": "https://fedoraproject.org/wiki/Licensing/Abstyles",
    },
    "AFL-1.1": {
        "name": "Academic Free License v1.1",
        "url": "http://opensource.linux-mirror.org/licenses/afl-1.1.txt",
    },
    "AFL-1.2": {
        "name": "Academic Free License v1.2",
        "url": "http://opensource.linux-mirror.org/licenses/afl-1.2.txt",
    },
    "AFL-2.0": {
        "name": "Academic Free License v2.0",
        "url": "http://opensource.linux-mirror.org/licenses/afl-2.0.txt",
    },
    "AFL-2.1": {
        "name": "Academic Free License v2.1",
        "url": "http://opensource.linux-mirror.org/licenses/afl-2.1.txt",
    },
    "AFL-3.0": {
        "name": "Academic Free License v3.0",
        "url": "http://www.opensource.org/licenses/afl-3.0",
    },
    "AMPAS": {
        "name": "Academy of Motion Picture Arts and Sciences BSD",
        "url": "https://fedoraproject.org/wiki/Licensing/BSD#AMPASBSD",
    },
    "APL-1.0": {
        "name": "Adaptive Public License 1.0",
        "url": "http://www.opensource.org/licenses/APL-1.0",
    },
    "Adobe-Glyph": {
        "name": "Adobe Glyph List License",
        "url": "https://fedoraproject.org/wiki/Licensing/MIT#AdobeGlyph",
    },
    "APAFML": {
        "name": "Adobe Postscript AFM License",
        "url": "https://fedoraproject.org/wiki/Licensing/AdobePostscriptAFM",
    },
    "Adobe-2006": {
        "name": "Adobe Systems Incorporated Source Code License Agreement",
        "url": "https://fedoraproject.org/wiki/Licensing/AdobeLicense",
    },
    "AGPL-1.0": {
        "name": "Affero General Public License v1.0",
        "url": "http://www.affero.org/oagpl.html",
    },
    "Afmparse": {
        "name": "Afmparse License",
        "url": "https://fedoraproject.org/wiki/Licensing/Afmparse",
    },
    "Aladdin": {
        "name": "Aladdin Free Public License",
        "url": "http://pages.cs.wisc.edu/~ghost/doc/AFPL/6.01/Public.htm",
    },
    "ADSL": {
        "name": "Amazon Digital Services License",
        "url": "https://fedoraproject.org/wiki/Licensing/AmazonDigitalServicesLicense",
    },
    "AMDPLPA": {
        "name": "AMD's plpa_map.c License",
        "url": "https://fedoraproject.org/wiki/Licensing/AMD_plpa_map_License",
    },
    "ANTLR-PD": {
        "name": "ANTLR Software Rights Notice",
        "url": "http://www.antlr2.org/license.html",
    },
    "Apache-1.0": {
        "name": "Apache License 1.0",
        "url": "http://www.apache.org/licenses/LICENSE-1.0",
    },
    "Apache-1.1": {
        "name": "Apache License 1.1",
        "url": "http://apache.org/licenses/LICENSE-1.1",
    },
    "Apache-2.0": {
        "name": "Apache License 2.0",
        "url": "http://www.apache.org/licenses/LICENSE-2.0",
    },
    "AML": {
        "name": "Apple MIT License",
        "url": "https://fedoraproject.org/wiki/Licensing/Apple_MIT_License",
    },
    "APSL-1.0": {
        "name": "Apple Public Source License 1.0",
        "url": "https://fedoraproject.org/wiki/Licensing/Apple_Public_Source_License_1.0",
    },
    "APSL-1.2": {
        "name": "Apple Public Source License 1.2",
        "url": "http://www.samurajdata.se/opensource/mirror/licenses/apsl.php",
    },
    "APSL-2.0": {
        "name": "Apple Public Source License 2.0",
        "url": "http://www.opensource.apple.com/license/apsl/",
    },
    "Artistic-1.0": {
        "name": "Artistic License 1.0",
        "url": "http://opensource.org/licenses/Artistic-1.0",
    },
    "Artistic-1.0-Perl": {
        "name": "Artistic License 1.0 (Perl)",
        "url": "http://dev.perl.org/licenses/artistic.html",
    },
    "Artistic-1.0-cl8": {
        "name": "Artistic License 1.0 w/clause 8",
        "url": "http://opensource.org/licenses/Artistic-1.0",
    },
    "Artistic-2.0": {
        "name": "Artistic License 2.0",
        "url": "http://www.opensource.org/licenses/artistic-license-2.0",
    },
    "AAL": {
        "name": "Attribution Assurance License",
        "url": "http://www.opensource.org/licenses/attribution",
    },
    "Bahyph": {
        "name": "Bahyph License",
        "url": "https://fedoraproject.org/wiki/Licensing/Bahyph",
    },
    "Barr": {
        "name": "Barr License",
        "url": "https://fedoraproject.org/wiki/Licensing/Barr",
    },
    "Beerware": {
        "name": "Beerware License",
        "url": "https://fedoraproject.org/wiki/Licensing/Beerware",
    },
    "BitTorrent-1.1": {
        "name": "BitTorrent Open Source License v1.1",
        "url": "http://directory.fsf.org/wiki/License:BitTorrentOSL1.1",
    },
    "BSL-1.0": {
        "name": "Boost Software License 1.0",
        "url": "http://www.boost.org/LICENSE_1_0.txt",
    },
    "Borceux": {
        "name": "Borceux license",
        "url": "https://fedoraproject.org/wiki/Licensing/Borceux",
    },
    "BSD-2-Clause": {
        "name": "BSD 2-clause \"Simplified\" License",
        "url": "http://www.opensource.org/licenses/BSD-2-Clause",
    },
    "BSD-2-Clause-FreeBSD": {
        "name": "BSD 2-clause FreeBSD License",
        "url": "http://www.freebsd.org/copyright/freebsd-license.html",
    },
    "BSD-2-Clause-NetBSD": {
        "name": "BSD 2-clause NetBSD License",
        "url": "http://www.netbsd.org/about/redistribution.html#default",
    },
    "BSD-3-Clause": {
        "name": "BSD 3-clause \"New\" or \"Revised\" License",
        "url": "http://www.opensource.org/licenses/BSD-3-Clause",
    },
    "BSD-3-Clause-Clear": {
        "name": "BSD 3-clause Clear License",
        "url": "http://labs.metacarta.com/license-explanation.html#license",
    },
    "BSD-4-Clause": {
        "name": "BSD 4-clause \"Original\" or \"Old\" License",
        "url": "http://directory.fsf.org/wiki/License:BSD_4Clause",
    },
    "BSD-Protection": {
        "name": "BSD Protection License",
        "url": "https://fedoraproject.org/wiki/Licensing/BSD_Protection_License",
    },
    "BSD-3-Clause-Attribution": {
        "name": "BSD with attribution",
        "url": "https://fedoraproject.org/wiki/Licensing/BSD_with_Attribution",
    },
    "0BSD": {
        "name": "BSD Zero Clause License",
        "url": "http://landley.net/toybox/license.html ",
    },
    "BSD-4-Clause-UC": {
        "name": "BSD-4-Clause (University of California-Specific)",
        "url": "http://www.freebsd.org/copyright/license.html",
    },
    "bzip2-1.0.5": {
        "name": "bzip2 and libbzip2 License v1.0.5",
        "url": "http://bzip.org/1.0.5/bzip2-manual-1.0.5.html",
    },
    "bzip2-1.0.6": {
        "name": "bzip2 and libbzip2 License v1.0.6",
        "url": "https://github.com/asimonov-im/bzip2/blob/master/LICENSE",
    },
    "Caldera": {
        "name": "Caldera License",
        "url": "http://www.lemis.com/grog/UNIX/ancient-source-all.pdf",
    },
    "CECILL-1.0": {
        "name": "CeCILL Free Software License Agreement v1.0",
        "url": "http://www.cecill.info/licences/Licence_CeCILL_V1-fr.html",
    },
    "CECILL-1.1": {
        "name": "CeCILL Free Software License Agreement v1.1",
        "url": "http://www.cecill.info/licences/Licence_CeCILL_V1.1-US.html",
    },
    "CECILL-2.0": {
        "name": "CeCILL Free Software License Agreement v2.0",
        "url": "http://www.cecill.info/licences/Licence_CeCILL_V2-fr.html",
    },
    "CECILL-2.1": {
        "name": "CeCILL Free Software License Agreement v2.1",
        "url": "http://opensource.org/licenses/CECILL-2.1",
    },
    "CECILL-B": {
        "name": "CeCILL-B Free Software License Agreement",
        "url": "http://www.cecill.info/licences/Licence_CeCILL-B_V1-fr.html",
    },
    "CECILL-C": {
        "name": "CeCILL-C Free Software License Agreement",
        "url": "http://www.cecill.info/licences/Licence_CeCILL-C_V1-fr.html",
    },
    "ClArtistic": {
        "name": "Clarified Artistic License",
        "url": "http://www.ncftp.com/ncftp/doc/LICENSE.txt",
    },
    "MIT-CMU": {
        "name": "CMU License",
        "url": "https://fedoraproject.org/wiki/Licensing:MIT?rd=Licensing/MIT#CMU_Style",
    },
    "CNRI-Jython": {
        "name": "CNRI Jython License",
        "url": "http://www.jython.org/license.html",
    },
    "CNRI-Python": {
        "name": "CNRI Python License",
        "url": "http://www.opensource.org/licenses/CNRI-Python",
    },
    "CNRI-Python-GPL-Compatible": {
        "name": "CNRI Python Open Source GPL Compatible License Agreement",
        "url": "http://www.python.org/download/releases/1.6.1/download_win/",
    },
    "CPOL-1.02": {
        "name": "Code Project Open License 1.02",
        "url": "http://www.codeproject.com/info/cpol10.aspx",
    },
    "CDDL-1.0": {
        "name": "Common Development and Distribution License 1.0",
        "url": "http://www.opensource.org/licenses/cddl1",
    },
    "CDDL-1.1": {
        "name": "Common Development and Distribution License 1.1",
        "url": "http://glassfish.java.net/public/CDDL+GPL_1_1.html",
    },
    "CPAL-1.0": {
        "name": "Common Public Attribution License 1.0",
        "url": "http://www.opensource.org/licenses/CPAL-1.0",
    },
    "CPL-1.0": {
        "name": "Common Public License 1.0",
        "url": "http://opensource.org/licenses/CPL-1.0",
    },
    "CATOSL-1.1": {
        "name": "Computer Associates Trusted Open Source License 1.1",
        "url": "http://opensource.org/licenses/CATOSL-1.1",
    },
    "Condor-1.1": {
        "name": "Condor Public License v1.1",
        "url": "http://research.cs.wisc.edu/condor/license.html#condor",
    },
    "CC-BY-1.0": {
        "name": "Creative Commons Attribution 1.0",
        "url": "https://creativecommons.org/licenses/by/1.0/",
    },
    "CC-BY-2.0": {
        "name": "Creative Commons Attribution 2.0",
        "url": "https://creativecommons.org/licenses/by/2.0/",
    },
    "CC-BY-2.5": {
        "name": "Creative Commons Attribution 2.5",
        "url": "https://creativecommons.org/licenses/by/2.5/",
    },
    "CC-BY-3.0": {
        "name": "Creative Commons Attribution 3.0",
        "url": "https://creativecommons.org/licenses/by/3.0/",
    },
    "CC-BY-4.0": {
        "name": "Creative Commons Attribution 4.0",
        "url": "https://creativecommons.org/licenses/by/4.0/",
    },
    "CC-BY-ND-1.0": {
        "name": "Creative Commons Attribution No Derivatives 1.0",
        "url": "https://creativecommons.org/licenses/by-nd/1.0/",
    },
    "CC-BY-ND-2.0": {
        "name": "Creative Commons Attribution No Derivatives 2.0",
        "url": "https://creativecommons.org/licenses/by-nd/2.0/",
    },
    "CC-BY-ND-2.5": {
        "name": "Creative Commons Attribution No Derivatives 2.5",
        "url": "https://creativecommons.org/licenses/by-nd/2.5/",
    },
    "CC-BY-ND-3.0": {
        "name": "Creative Commons Attribution No Derivatives 3.0",
        "url": "https://creativecommons.org/licenses/by-nd/3.0/",
    },
    "CC-BY-ND-4.0": {
        "name": "Creative Commons Attribution No Derivatives 4.0",
        "url": "https://creativecommons.org/licenses/by-nd/4.0/",
    },
    "CC-BY-NC-1.0": {
        "name": "Creative Commons Attribution Non Commercial 1.0",
        "url": "https://creativecommons.org/licenses/by-nc/1.0/",
    },
    "CC-BY-NC-2.0": {
        "name": "Creative Commons Attribution Non Commercial 2.0",
        "url": "https://creativecommons.org/licenses/by-nc/2.0/",
    },
    "CC-BY-NC-2.5": {
        "name": "Creative Commons Attribution Non Commercial 2.5",
        "url": "https://creativecommons.org/licenses/by-nc/2.5/",
    },
    "CC-BY-NC-3.0": {
        "name": "Creative Commons Attribution Non Commercial 3.0",
        "url": "https://creativecommons.org/licenses/by-nc/3.0/",
    },
    "CC-BY-NC-4.0": {
        "name": "Creative Commons Attribution Non Commercial 4.0",
        "url": "https://creativecommons.org/licenses/by-nc/4.0/",
    },
    "CC-BY-NC-ND-1.0": {
        "name": "Creative Commons Attribution Non Commercial No Derivatives 1.0",
        "url": "https://creativecommons.org/licenses/by-nd-nc/1.0/",
    },
    "CC-BY-NC-ND-2.0": {
        "name": "Creative Commons Attribution Non Commercial No Derivatives 2.0",
        "url": "https://creativecommons.org/licenses/by-nc-nd/2.0/",
    },
    "CC-BY-NC-ND-2.5": {
        "name": "Creative Commons Attribution Non Commercial No Derivatives 2.5",
        "url": "https://creativecommons.org/licenses/by-nc-nd/2.5/",
    },
    "CC-BY-NC-ND-3.0": {
        "name": "Creative Commons Attribution Non Commercial No Derivatives 3.0",
        "url": "https://creativecommons.org/licenses/by-nc-nd/3.0/",
    },
    "CC-BY-NC-ND-4.0": {
        "name": "Creative Commons Attribution Non Commercial No Derivatives 4.0",
        "url": "https://creativecommons.org/licenses/by-nc-nd/4.0/",
    },
    "CC-BY-NC-SA-1.0": {
        "name": "Creative Commons Attribution Non Commercial Share Alike 1.0",
        "url": "https://creativecommons.org/licenses/by-nc-sa/1.0/",
    },
    "CC-BY-NC-SA-2.0": {
        "name": "Creative Commons Attribution Non Commercial Share Alike 2.0",
        "url": "https://creativecommons.org/licenses/by-nc-sa/2.0/",
    },
    "CC-BY-NC-SA-2.5": {
        "name": "Creative Commons Attribution Non Commercial Share Alike 2.5",
        "url": "https://creativecommons.org/licenses/by-nc-sa/2.5/",
    },
    "CC-BY-NC-SA-3.0": {
        "name": "Creative Commons Attribution Non Commercial Share Alike 3.0",
        "url": "https://creativecommons.org/licenses/by-nc-sa/3.0/",
    },
    "CC-BY-NC-SA-4.0": {
        "name": "Creative Commons Attribution Non Commercial Share Alike 4.0",
        "url": "https://creativecommons.org/licenses/by-nc-sa/4.0/",
    },
    "CC-BY-SA-1.0": {
        "name": "Creative Commons Attribution Share Alike 1.0",
        "url": "https://creativecommons.org/licenses/by-sa/1.0/",
    },
    "CC-BY-SA-2.0": {
        "name": "Creative Commons Attribution Share Alike 2.0",
        "url": "https://creativecommons.org/licenses/by-sa/2.0/",
    },
    "CC-BY-SA-2.5": {
        "name": "Creative Commons Attribution Share Alike 2.5",
        "url": "https://creativecommons.org/licenses/by-sa/2.5/",
    },
    "CC-BY-SA-3.0": {
        "name": "Creative Commons Attribution Share Alike 3.0",
        "url": "https://creativecommons.org/licenses/by-sa/3.0/",
    },
    "CC-BY-SA-4.0": {
        "name": "Creative Commons Attribution Share Alike 4.0",
        "url": "https://creativecommons.org/licenses/by-sa/4.0/",
    },
    "CC0-1.0": {
        "name": "Creative Commons Zero v1.0 Universal",
        "url": "https://creativecommons.org/publicdomain/zero/1.0/",
    },
    "Crossword": {
        "name": "Crossword License",
        "url": "https://fedoraproject.org/wiki/Licensing/Crossword",
    },
    "CUA-OPL-1.0": {
        "name": "CUA Office Public License v1.0",
        "url": "http://opensource.org/licenses/CUA-OPL-1.0",
    },
    "Cube": {
        "name": "Cube License",
        "url": "https://fedoraproject.org/wiki/Licensing/Cube",
    },
    "D-FSL-1.0": {
        "name": "Deutsche Freie Software Lizenz",
        "url": "http://www.dipp.nrw.de/d-fsl/index_html/lizenzen/de/D-FSL-1_0_de.txt",
    },
    "diffmark": {
        "name": "diffmark license",
        "url": "https://fedoraproject.org/wiki/Licensing/diffmark",
    },
    "WTFPL": {
        "name": "Do What The F*ck You Want To Public License",
        "url": "http://sam.zoy.org/wtfpl/COPYING",
    },
    "DOC": {
        "name": "DOC License",
        "url": "http://www.cs.wustl.edu/~schmidt/ACE-copying.html",
    },
    "Dotseqn": {
        "name": "Dotseqn License",
        "url": "https://fedoraproject.org/wiki/Licensing/Dotseqn",
    },
    "DSDP": {
        "name": "DSDP License",
        "url": "https://fedoraproject.org/wiki/Licensing/DSDP",
    },
    "dvipdfm": {
        "name": "dvipdfm License",
        "url": "https://fedoraproject.org/wiki/Licensing/dvipdfm",
    },
    "EPL-1.0": {
        "name": "Eclipse Public License 1.0",
        "url": "http://www.opensource.org/licenses/EPL-1.0",
    },
    "ECL-1.0": {
        "name": "Educational Community License v1.0",
        "url": "http://opensource.org/licenses/ECL-1.0",
    },
    "ECL-2.0": {
        "name": "Educational Community License v2.0",
        "url": "http://opensource.org/licenses/ECL-2.0",
    },
    "EFL-1.0": {
        "name": "Eiffel Forum License v1.0",
        "url": "http://opensource.org/licenses/EFL-1.0",
    },
    "EFL-2.0": {
        "name": "Eiffel Forum License v2.0",
        "url": "http://opensource.org/licenses/EFL-2.0",
    },
    "MIT-advertising": {
        "name": "Enlightenment License (e16)",
        "url": "https://fedoraproject.org/wiki/Licensing/MIT_With_Advertising",
    },
    "MIT-enna": {
        "name": "enna License",
        "url": "https://fedoraproject.org/wiki/Licensing/MIT#enna",
    },
    "Entessa": {
        "name": "Entessa Public License v1.0",
        "url": "http://opensource.org/licenses/Entessa",
    },
    "ErlPL-1.1": {
        "name": "Erlang Public License v1.1",
        "url": "http://www.erlang.org/EPLICENSE",
    },
    "EUDatagrid": {
        "name": "EU DataGrid Software License",
        "url": "http://www.opensource.org/licenses/EUDatagrid",
    },
    "EUPL-1.0": {
        "name": "European Union Public License 1.0",
        "url": "http://ec.europa.eu/idabc/en/document/7330.html",
    },
    "EUPL-1.1": {
        "name": "European Union Public License 1.1",
        "url": "http://www.opensource.org/licenses/EUPL-1.1",
    },
    "Eurosym": {
        "name": "Eurosym License",
        "url": "https://fedoraproject.org/wiki/Licensing/Eurosym",
    },
    "Fair": {
        "name": "Fair License",
        "url": "http://www.opensource.org/licenses/Fair",
    },
    "MIT-feh": {
        "name": "feh License",
        "url": "https://fedoraproject.org/wiki/Licensing/MIT#feh",
    },
    "Frameworx-1.0": {
        "name": "Frameworx Open License 1.0",
        "url": "http://www.opensource.org/licenses/Frameworx-1.0",
    },
    "FreeImage": {
        "name": "FreeImage Public License v1.0",
        "url": "http://freeimage.sourceforge.net/freeimage-license.txt",
    },
    "FTL": {
        "name": "Freetype Project License",
        "url": "http://freetype.fis.uniroma2.it/FTL.TXT",
    },
    "FSFUL": {
        "name": "FSF Unlimited License",
        "url": "https://fedoraproject.org/wiki/Licensing/FSF_Unlimited_License",
    },
    "FSFULLR": {
        "name": "FSF Unlimited License (with License Retention)",
        "url": "https://fedoraproject.org/wiki/Licensing/FSF_Unlimited_License",
    },
    "Giftware": {
        "name": "Giftware License",
        "url": "http://alleg.sourceforge.net//license.html",
    },
    "GL2PS": {
        "name": "GL2PS License",
        "url": "http://www.geuz.org/gl2ps/COPYING.GL2PS",
    },
    "Glulxe": {
        "name": "Glulxe License",
        "url": "https://fedoraproject.org/wiki/Licensing/Glulxe",
    },
    "AGPL-3.0": {
        "name": "GNU Affero General Public License v3.0",
        "url": "http://www.gnu.org/licenses/agpl.txt",
    },
    "GFDL-1.1": {
        "name": "GNU Free Documentation License v1.1",
        "url": "http://www.gnu.org/licenses/old-licenses/fdl-1.1.txt",
    },
    "GFDL-1.2": {
        "name": "GNU Free Documentation License v1.2",
        "url": "http://www.gnu.org/licenses/old-licenses/fdl-1.2.txt",
    },
    "GFDL-1.3": {
        "name": "GNU Free Documentation License v1.3",
        "url": "http://www.gnu.org/licenses/fdl-1.3.txt",
    },
    "GPL-1.0": {
        "name": "GNU General Public License v1.0 only",
        "url": "http://www.gnu.org/licenses/old-licenses/gpl-1.0-standalone.html",
    },
    "GPL-2.0": {
        "name": "GNU General Public License v2.0 only",
        "url": "http://www.opensource.org/licenses/GPL-2.0",
    },
    "GPL-3.0": {
        "name": "GNU General Public License v3.0 only",
        "url": "http://www.opensource.org/licenses/GPL-3.0",
    },
    "LGPL-2.1": {
        "name": "GNU Lesser General Public License v2.1 only",
        "url": "http://www.opensource.org/licenses/LGPL-2.1",
    },
    "LGPL-3.0": {
        "name": "GNU Lesser General Public License v3.0 only",
        "url": "http://www.opensource.org/licenses/LGPL-3.0",
    },
    "LGPL-2.0": {
        "name": "GNU Library General Public License v2 only",
        "url": "http://www.gnu.org/licenses/old-licenses/lgpl-2.0-standalone.html",
    },
    "gnuplot": {
        "name": "gnuplot License",
        "url": "https://fedoraproject.org/wiki/Licensing/Gnuplot",
    },
    "gSOAP-1.3b": {
        "name": "gSOAP Public License v1.3b",
        "url": "http://www.cs.fsu.edu/~engelen/license.html",
    },
    "HaskellReport": {
        "name": "Haskell Language Report License",
        "url": "https://fedoraproject.org/wiki/Licensing/Haskell_Language_Report_License",
    },
    "HPND": {
        "name": "Historic Permission Notice and Disclaimer",
        "url": "http://www.opensource.org/licenses/HPND",
    },
    "IPL-1.0": {
        "name": "IBM Public License v1.0",
        "url": "http://www.opensource.org/licenses/IPL-1.0",
    },
    "ICU": {
        "name": "ICU License",
        "url": "http://source.icu-project.org/repos/icu/icu/trunk/license.html",
    },
    "ImageMagick": {
        "name": "ImageMagick License",
        "url": "http://www.imagemagick.org/script/license.php",
    },
    "iMatix": {
        "name": "iMatix Standard Function Library Agreement",
        "url": "http://legacy.imatix.com/html/sfl/sfl4.htm#license",
    },
    "Imlib2": {
        "name": "Imlib2 License",
        "url": "http://trac.enlightenment.org/e/browser/trunk/imlib2/COPYING",
    },
    "IJG": {
        "name": "Independent JPEG Group License",
        "url": "http://dev.w3.org/cvsweb/Amaya/libjpeg/Attic/README?rev=1.2",
    },
    "Intel": {
        "name": "Intel Open Source License",
        "url": "http://opensource.org/licenses/Intel",
    },
    "IPA": {
        "name": "IPA Font License",
        "url": "http://www.opensource.org/licenses/IPA",
    },
    "JasPer-2.0": {
        "name": "JasPer License",
        "url": "http://www.ece.uvic.ca/~mdadams/jasper/LICENSE",
    },
    "JSON": {
        "name": "JSON License",
        "url": "http://www.json.org/license.html",
    },
    "LPPL-1.3a": {
        "name": "LaTeX Project Public License 1.3a",
        "url": "http://www.latex-project.org/lppl/lppl-1-3a.txt",
    },
    "LPPL-1.0": {
        "name": "LaTeX Project Public License v1.0",
        "url": "http://www.latex-project.org/lppl/lppl-1-0.txt",
    },
    "LPPL-1.1": {
        "name": "LaTeX Project Public License v1.1",
        "url": "http://www.latex-project.org/lppl/lppl-1-1.txt",
    },
    "LPPL-1.2": {
        "name": "LaTeX Project Public License v1.2",
        "url": "http://www.latex-project.org/lppl/lppl-1-2.txt",
    },
    "LPPL-1.3c": {
        "name": "LaTeX Project Public License v1.3c",
        "url": "http://www.opensource.org/licenses/LPPL-1.3c",
    },
    "Latex2e": {
        "name": "Latex2e License",
        "url": "https://fedoraproject.org/wiki/Licensing/Latex2e",
    },
    "BSD-3-Clause-LBNL": {
        "name": "Lawrence Berkeley National Labs BSD variant license",
        "url": "https://fedoraproject.org/wiki/Licensing/LBNLBSD",
    },
    "Leptonica": {
        "name": "Leptonica License",
        "url": "https://fedoraproject.org/wiki/Licensing/Leptonica",
    },
    "LGPLLR": {
        "name": "Lesser General Public License For Linguistic Resources",
        "url": "http://www-igm.univ-mlv.fr/~unitex/lgpllr.html",
    },
    "Libpng": {
        "name": "libpng License",
        "url": "http://www.libpng.org/pub/png/src/libpng-LICENSE.txt",
    },
    "libtiff": {
        "name": "libtiff License",
        "url": "https://fedoraproject.org/wiki/Licensing/libtiff",
    },
    "LPL-1.02": {
        "name": "Lucent Public License v1.02",
        "url": "http://www.opensource.org/licenses/LPL-1.02",
    },
    "LPL-1.0": {
        "name": "Lucent Public License Version 1.0",
        "url": "http://opensource.org/licenses/LPL-1.0",
    },
    "MakeIndex": {
        "name": "MakeIndex License",
        "url": "https://fedoraproject.org/wiki/Licensing/MakeIndex",
    },
    "MTLL": {
        "name": "Matrix Template Library License",
        "url": "https://fedoraproject.org/wiki/Licensing/Matrix_Template_Library_License",
    },
    "MS-PL": {
        "name": "Microsoft Public License",
        "url": "http://www.opensource.org/licenses/MS-PL",
    },
    "MS-RL": {
        "name": "Microsoft Reciprocal License",
        "url": "http://www.opensource.org/licenses/MS-RL",
    },
    "MirOS": {
        "name": "MirOS Licence",
        "url": "http://www.opensource.org/licenses/MirOS",
    },
    "MITNFA": {
        "name": "MIT +no-false-attribs license",
        "url": "https://fedoraproject.org/wiki/Licensing/MITNFA",
    },
    "MIT": {
        "name": "MIT License",
        "url": "http://www.opensource.org/licenses/MIT",
    },
    "Motosoto": {
        "name": "Motosoto License",
        "url": "http://www.opensource.org/licenses/Motosoto",
    },
    "MPL-1.0": {
        "name": "Mozilla Public License 1.0",
        "url": "http://www.mozilla.org/MPL/MPL-1.0.html",
    },
    "MPL-1.1": {
        "name": "Mozilla Public License 1.1",
        "url": "http://www.mozilla.org/MPL/MPL-1.1.html",
    },
    "MPL-2.0": {
        "name": "Mozilla Public License 2.0",
        "url": "http://www.mozilla.org/MPL/2.0/\nhttp://opensource.org/licenses/MPL-2.0",
    },
    "MPL-2.0-no-copyleft-exception": {
        "name": "Mozilla Public License 2.0 (no copyleft exception)",
        "url": "http://www.mozilla.org/MPL/2.0/\nhttp://opensource.org/licenses/MPL-2.0",
    },
    "mpich2": {
        "name": "mpich2 License",
        "url": "https://fedoraproject.org/wiki/Licensing/MIT",
    },
    "Multics": {
        "name": "Multics License",
        "url": "http://www.opensource.org/licenses/Multics",
    },
    "Mup": {
        "name": "Mup License",
        "url": "https://fedoraproject.org/wiki/Licensing/Mup",
    },
    "NASA-1.3": {
        "name": "NASA Open Source Agreement 1.3",
        "url": "http://www.opensource.org/licenses/NASA-1.3",
    },
    "Naumen": {
        "name": "Naumen Public License",
        "url": "http://www.opensource.org/licenses/Naumen",
    },
    "NetCDF": {
        "name": "NetCDF license",
        "url": "http://www.unidata.ucar.edu/software/netcdf/copyright.html",
    },
    "NGPL": {
        "name": "Nethack General Public License",
        "url": "http://www.opensource.org/licenses/NGPL",
    },
    "NOSL": {
        "name": "Netizen Open Source License",
        "url": "http://bits.netizen.com.au/licenses/NOSL/nosl.txt",
    },
    "NPL-1.0": {
        "name": "Netscape Public License v1.0",
        "url": "http://www.mozilla.org/MPL/NPL/1.0/",
    },
    "NPL-1.1": {
        "name": "Netscape Public License v1.1",
        "url": "http://www.mozilla.org/MPL/NPL/1.1/",
    },
    "Newsletr": {
        "name": "Newsletr License",
        "url": "https://fedoraproject.org/wiki/Licensing/Newsletr",
    },
    "NLPL": {
        "name": "No Limit Public License",
        "url": "https://fedoraproject.org/wiki/Licensing/NLPL",
    },
    "Nokia": {
        "name": "Nokia Open Source License",
        "url": "http://www.opensource.org/licenses/nokia",
    },
    "NPOSL-3.0": {
        "name": "Non-Profit Open Software License 3.0",
        "url": "http://www.opensource.org/licenses/NOSL3.0",
    },
    "Noweb": {
        "name": "Noweb License",
        "url": "https://fedoraproject.org/wiki/Licensing/Noweb",
    },
    "NRL": {
        "name": "NRL License",
        "url": "http://web.mit.edu/network/isakmp/nrllicense.html",
    },
    "NTP": {
        "name": "NTP License",
        "url": "http://www.opensource.org/licenses/NTP",
    },
    "Nunit": {
        "name": "Nunit License",
        "url": "https://fedoraproject.org/wiki/Licensing/Nunit",
    },
    "OCLC-2.0": {
        "name": "OCLC Research Public License 2.0",
        "url": "http://www.opensource.org/licenses/OCLC-2.0",
    },
    "ODbL-1.0": {
        "name": "ODC Open Database License v1.0",
        "url": "http://www.opendatacommons.org/licenses/odbl/1.0/",
    },
    "PDDL-1.0": {
        "name": "ODC Public Domain Dedication & License 1.0",
        "url": "http://opendatacommons.org/licenses/pddl/1.0/",
    },
    "OGTSL": {
        "name": "Open Group Test Suite License",
        "url": "http://www.opensource.org/licenses/OGTSL",
    },
    "OML": {
        "name": "Open Market License",
        "url": "https://fedoraproject.org/wiki/Licensing/Open_Market_License",
    },
    "OPL-1.0": {
        "name": "Open Public License v1.0",
        "url": "https://fedoraproject.org/wiki/Licensing/Open_Public_License",
    },
    "OSL-1.0": {
        "name": "Open Software License 1.0",
        "url": "http://opensource.org/licenses/OSL-1.0",
    },
    "OSL-1.1": {
        "name": "Open Software License 1.1",
        "url": "https://fedoraproject.org/wiki/Licensing/OSL1.1",
    },
    "PHP-3.01": {
        "name": "PHP License v3.01",
        "url": "http://www.php.net/license/3_01.txt",
    },
    "Plexus": {
        "name": "Plexus Classworlds License",
        "url": "https://fedoraproject.org/wiki/Licensing/Plexus_Classworlds_License",
    },
    "PostgreSQL": {
        "name": "PostgreSQL License",
        "url": "http://www.opensource.org/licenses/PostgreSQL",
    },
    "psfrag": {
        "name": "psfrag License",
        "url": "https://fedoraproject.org/wiki/Licensing/psfrag",
    },
    "psutils": {
        "name": "psutils License",
        "url": "https://fedoraproject.org/wiki/Licensing/psutils",
    },
    "Python-2.0": {
        "name": "Python License 2.0",
        "url": "http://www.opensource.org/licenses/Python-2.0",
    },
    "QPL-1.0": {
        "name": "Q Public License 1.0",
        "url": "http://www.opensource.org/licenses/QPL-1.0",
    },
    "Qhull": {
        "name": "Qhull License",
        "url": "https://fedoraproject.org/wiki/Licensing/Qhull",
    },
    "Rdisc": {
        "name": "Rdisc License",
        "url": "https://fedoraproject.org/wiki/Licensing/Rdisc_License",
    },
    "RPSL-1.0": {
        "name": "RealNetworks Public Source License v1.0",
        "url": "http://www.opensource.org/licenses/RPSL-1.0",
    },
    "RPL-1.1": {
        "name": "Reciprocal Public License 1.1",
        "url": "http://opensource.org/licenses/RPL-1.1",
    },
    "RPL-1.5": {
        "name": "Reciprocal Public License 1.5",
        "url": "http://www.opensource.org/licenses/RPL-1.5",
    },
    "RHeCos-1.1": {
        "name": "Red Hat eCos Public License v1.1",
        "url": "http://ecos.sourceware.org/old-license.html",
    },
    "RSCPL": {
        "name": "Ricoh Source Code Public License",
        "url": "http://www.opensource.org/licenses/RSCPL",
    },
    "RSA-MD": {
        "name": "RSA Message-Digest License",
        "url": "http://www.faqs.org/rfcs/rfc1321.html",
    },
    "Ruby": {
        "name": "Ruby License",
        "url": "http://www.ruby-lang.org/en/LICENSE.txt",
    },
    "SAX-PD": {
        "name": "Sax Public Domain Notice",
        "url": "http://www.saxproject.org/copying.html",
    },
    "Saxpath": {
        "name": "Saxpath License",
        "url": "https://fedoraproject.org/wiki/Licensing/Saxpath_License",
    },
    "SCEA": {
        "name": "SCEA Shared Source License",
        "url": "http://research.scea.com/scea_shared_source_license.html",
    },
    "SWL": {
        "name": "Scheme Widget Library (SWL) Software License Agreement",
        "url": "https://fedoraproject.org/wiki/Licensing/SWL",
    },
    "Sendmail": {
        "name": "Sendmail License",
        "url": "http://www.sendmail.com/pdfs/open_source/sendmail_license.pdf",
    },
    "SGI-B-1.0": {
        "name": "SGI Free Software License B v1.0",
        "url": "http://oss.sgi.com/projects/FreeB/SGIFreeSWLicB.1.0.html",
    },
    "SGI-B-1.1": {
        "name": "SGI Free Software License B v1.1",
        "url": "http://oss.sgi.com/projects/FreeB/",
    },
    "SGI-B-2.0": {
        "name": "SGI Free Software License B v2.0",
        "url": "http://oss.sgi.com/projects/FreeB/SGIFreeSWLicB.2.0.pdf",
    },
    "OFL-1.0": {
        "name": "SIL Open Font License 1.0",
        "url": "http://scripts.sil.org/cms/scripts/page.php?item_id=OFL10_web",
    },
    "OFL-1.1": {
        "name": "SIL Open Font License 1.1",
        "url": "http://www.opensource.org/licenses/OFL-1.1",
    },
    "SimPL-2.0": {
        "name": "Simple Public License 2.0",
        "url": "http://www.opensource.org/licenses/SimPL-2.0",
    },
    "Sleepycat": {
        "name": "Sleepycat License",
        "url": "http://www.opensource.org/licenses/Sleepycat",
    },
    "SNIA": {
        "name": "SNIA Public License 1.1",
        "url": "https://fedoraproject.org/wiki/Licensing/SNIA_Public_License",
    },
    "SMLNJ": {
        "name": "Standard ML of New Jersey License",
        "url": "http://www.smlnj.org//license.html",
    },
    "SugarCRM-1.1.3": {
        "name": "SugarCRM Public License v1.1.3",
        "url": "http://www.sugarcrm.com/crm/SPL",
    },
    "SISSL": {
        "name": "Sun Industry Standards Source License v1.1",
        "url": "http://opensource.org/licenses/SISSL",
    },
    "SISSL-1.2": {
        "name": "Sun Industry Standards Source License v1.2",
        "url": "http://gridscheduler.sourceforge.net/Gridengine_SISSL_license.html",
    },
    "SPL-1.0": {
        "name": "Sun Public License v1.0",
        "url": "http://www.opensource.org/licenses/SPL-1.0",
    },
    "Watcom-1.0": {
        "name": "Sybase Open Watcom Public License 1.0",
        "url": "http://www.opensource.org/licenses/Watcom-1.0",
    },
    "TCL": {
        "name": "TCL/TK License",
        "url": "https://fedoraproject.org/wiki/Licensing/TCL",
    },
    "Unlicense": {
        "name": "The Unlicense",
        "url": "http://unlicense.org/",
    },
    "TMate": {
        "name": "TMate Open Source License",
        "url": "http://svnkit.com/license.html",
    },
    "TORQUE-1.1": {
        "name": "TORQUE v2.5+ Software License v1.1",
        "url": "https://fedoraproject.org/wiki/Licensing/TORQUEv1.1",
    },
    "TOSL": {
        "name": "Trusster Open Source License",
        "url": "https://fedoraproject.org/wiki/Licensing/TOSL",
    },
    "Unicode-TOU": {
        "name": "Unicode Terms of Use",
        "url": "http://www.unicode.org/copyright.html",
    },
    "UPL-1.0": {
        "name": "Universal Permissive License v1.0",
        "url": "http://opensource.org/licenses/UPL",
    },
    "NCSA": {
        "name": "University of Illinois/NCSA Open Source License",
        "url": "http://www.opensource.org/licenses/NCSA",
    },
    "Vim": {
        "name": "Vim License",
        "url": "http://vimdoc.sourceforge.net/htmldoc/uganda.html",
    },
    "VOSTROM": {
        "name": "VOSTROM Public License for Open Source",
        "url": "https://fedoraproject.org/wiki/Licensing/VOSTROM",
    },
    "VSL-1.0": {
        "name": "Vovida Software License v1.0",
        "url": "http://www.opensource.org/licenses/VSL-1.0",
    },
    "W3C-19980720": {
        "name": "W3C Software Notice and License (1998-07-20)",
        "url": "http://www.w3.org/Consortium/Legal/copyright-software-19980720.html",
    },
    "W3C": {
        "name": "W3C Software Notice and License (2002-12-31)",
        "url": "http://www.opensource.org/licenses/W3C",
    },
    "Wsuipa": {
        "name": "Wsuipa License",
        "url": "https://fedoraproject.org/wiki/Licensing/Wsuipa",
    },
    "Xnet": {
        "name": "X.Net License",
        "url": "http://opensource.org/licenses/Xnet",
    },
    "X11": {
        "name": "X11 License",
        "url": "http://www.xfree86.org/3.3.6/COPYRIGHT2.html#3",
    },
    "Xerox": {
        "name": "Xerox License",
        "url": "https://fedoraproject.org/wiki/Licensing/Xerox",
    },
    "XFree86-1.1": {
        "name": "XFree86 License 1.1",
        "url": "http://www.xfree86.org/current/LICENSE4.html",
    },
    "xinetd": {
        "name": "xinetd License",
        "url": "https://fedoraproject.org/wiki/Licensing/Xinetd_License",
    },
    "xpp": {
        "name": "XPP License",
        "url": "https://fedoraproject.org/wiki/Licensing/xpp",
    },
    "XSkat": {
        "name": "XSkat License",
        "url": "https://fedoraproject.org/wiki/Licensing/XSkat_License",
    },
    "YPL-1.0": {
        "name": "Yahoo! Public License v1.0",
        "url": "http://www.zimbra.com/license/yahoo_public_license_1.0.html",
    },
    "YPL-1.1": {
        "name": "Yahoo! Public License v1.1",
        "url": "http://www.zimbra.com/license/yahoo_public_license_1.1.html",
    },
    "Zed": {
        "name": "Zed License",
        "url": "https://fedoraproject.org/wiki/Licensing/Zed",
    },
    "Zlib": {
        "name": "zlib License",
        "url": "http://www.opensource.org/licenses/Zlib",
    },
    "zlib-acknowledgement": {
        "name": "zlib/libpng License with Acknowledgement",
        "url": "https://fedoraproject.org/wiki/Licensing/ZlibWithAcknowledgement",
    },
    "ZPL-1.1": {
        "name": "Zope Public License 1.1",
        "url": "http://old.zope.org/Resources/License/ZPL-1.1",
    },
    "ZPL-2.0": {
        "name": "Zope Public License 2.0",
        "url": "http://opensource.org/licenses/ZPL-2.0",
    },
    "ZPL-2.1": {
        "name": "Zope Public License 2.1",
        "url": "http://old.zope.org/Resources/ZPL/",
    }
}


@attr.s
class License(object):
    id = attr.ib()
    name = attr.ib()
    url = attr.ib()

    @property
    def legalcode(self):
        p = pathlib.Path(__file__).parent / 'legalcode' / self.id
        if p.exists():
            return p.read_text(encoding='utf8')


_LICENSES = [License(id_, l['name'], l['url']) for id_, l in _LICENSES.items()]


def find(q):
    for license_ in _LICENSES:
        if q.lower() == license_.id.lower() or q == license_.name or q == license_.url:
            return license_
        if '://' in q:
            u1 = license_.url.split('://')[1]
            u2 = q.split('://')[1]
            if u1.startswith(u2) or u2.startswith(u1):
                return license_
