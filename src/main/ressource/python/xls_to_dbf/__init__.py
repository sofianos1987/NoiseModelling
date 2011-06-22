import pyExcelerator as xlst
import dbfUtils
import sys


##
# Function creator
# @return A function that return the cellid of a parameter
def GetCell(cellid):
    def Get(obj):
        return obj[cellid]
    return Get
##
# Open an XLS file and return all extracted data
def ParseXlsData(filename):
    return xlst.parse_xls(filename)
##
# Filter xls data
# Return fields and cell values. As a tuple (fields,cell_data)
def FilterXlsData(data,sheetid,startline,range_col_id,fieldline):
    range_row_id=range(startline,max(data[sheetid][1].keys(),key=GetCell(0))[0]+1)
    fields=[data[sheetid][1].get((fieldline,idcol),None) for idcol in range_col_id ]
    ext_data=[[data[sheetid][1].get((idrow,idcol),None) for idcol in range_col_id ] for idrow in range_row_id]
    return fields,ext_data
###
# Open an XLS file and extract a range of cell
# None cell is empty cell
# @Return tuple (fields list, list of cols within list of rows)
def ExtractXlsData(filename,sheetid,startline,range_col_id,fieldline):
    #Open XLS file
    data=ParseXlsData(filename)
    #Extract valid cell_id
    return FilterXlsData(data,sheetid,startline,range_col_id,fieldline)

def GetFuncReturnDefaultWhenNone(defaultvalue):
    def BaseFunc(val):
        if val is None:
            return defaultvalue
        else:
            return val
    return BaseFunc

def SetDefaultValueWhereNone(fields):
    type_to_default={str : "" , unicode : u"", int : 0 , float : 0.}
    if None in fields[0]:
        rotfields=zip(*fields)
        for idcol,col in enumerate(rotfields):
            if col[0] is None:
                firstval=max(col)
                if not firstval is None:
                    #Replace None values by default value as specified in type_to_default dictionnary
                    rotfields[idcol]=map(GetFuncReturnDefaultWhenNone(type_to_default[firstval.__class__]),col)
                else:
                    sys.stderr.write(u"Unspecified column type, use integer(0) instead of None")
                    rotfields[idcol]=[0 for i in range(len(col))]
        return zip(*rotfields)
    else:
        return fields
            
def GetFieldSpecs(fields,array):
    python_to_dbase={ "str" : ('C', 255, 0), "int" : ('N', 10, 0), "unicode" : ('C', 255, 0), "float" : ('N', 24, 15) }
    fspecs=[]
    rotarray=zip(*array)
    for idfield,field in enumerate(array[0]):
        field_type_found=False
        for python_type,dbasetype in python_to_dbase.iteritems():
            if isinstance(field,eval(python_type)):
                col_kind_tuple=python_to_dbase[python_type]
                if python_type=="str":
                    #Compute the best fitting size
                    col_kind_tuple=(col_kind_tuple[0],max(map(len,rotarray[idfield]))+1,col_kind_tuple[2])
                fspecs.append(col_kind_tuple)
                field_type_found=True
                break
        if not field_type_found:
            fspecs.append(python_to_dbase["float"])
    return fspecs
def SaveArrayToDBF(filename,fields,array):
    
    f=open(filename,"wb") #open a file for write in binary mode
    field_specs=GetFieldSpecs(fields,array)
    dbfUtils.dbfwriter(f,map(ToFormatedField,fields),field_specs,array)
    f.close()
##
# Convert unicode field to dbase compatible field name
def ToFormatedField(unicodeField):
    return unicodeField.encode('cp1252')[:10]