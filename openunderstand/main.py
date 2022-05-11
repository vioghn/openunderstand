"""

"""

import os
from fnmatch import fnmatch

from antlr4 import *

from gen.javaLabeled.JavaParserLabeled import JavaParserLabeled
from gen.javaLabeled.JavaLexer import JavaLexer

from oudb.models import KindModel, EntityModel, ReferenceModel
from oudb.api import open as db_open, create_db
from oudb.fill import main

from analysis_passes.couple_coupleby import ImplementCoupleAndImplementByCoupleBy
from analysis_passes.create_createby import CreateAndCreateBy
from analysis_passes.declare_declarein import DeclareAndDeclareinListener
from analysis_passes.class_properties import ClassPropertiesListener, InterfacePropertiesListener
from analysis_passes.import_importby import ImportListener
from openunderstand.override_overrideby import overridelistener
from openunderstand.couple_coupleby import CoupleAndCoupleBy


class Project():
    tree = None

    def Parse(self, fileAddress):
        file_stream = FileStream(fileAddress)
        lexer = JavaLexer(file_stream)
        tokens = CommonTokenStream(lexer)
        parser = JavaParserLabeled(tokens)
        tree = parser.compilationUnit()
        self.tree = tree
        return tree

    def Walk(self, listener, tree):
        walker = ParseTreeWalker()
        walker.walk(listener=listener, t=tree)

    def getListOfFiles(self, dirName):
        listOfFile = os.listdir(dirName)
        allFiles = list()
        for entry in listOfFile:
            # Create full path
            fullPath = os.path.join(dirName, entry)
            if os.path.isdir(fullPath):
                allFiles = allFiles + self.getListOfFiles(fullPath)
            elif fnmatch(fullPath, "*.java"):
                allFiles.append(fullPath)

        return allFiles

    def getFileEntity(self, path):
        # kind id: 1
        path = path.replace("/", "\\")
        name = path.split("\\")[-1]
        file = open(path, mode='r')
        file_ent = EntityModel.get_or_create(_kind=1, _name=name, _longname=path, _contents=file.read())[0]
        file.close()
        print("processing file:", file_ent)
        return file_ent

    def addDeclareRefs(self, ref_dicts, file_ent):
        for ref_dict in ref_dicts:
            if ref_dict["scope"] is None:  # the scope is the file
                scope = file_ent
            else:  # a normal package
                scope = self.getPackageEntity(file_ent, ref_dict["scope"], ref_dict["scope_longname"])

            if ref_dict["ent"] is None:  # the ent package is unnamed
                ent = self.getUnnamedPackageEntity(file_ent)
            else:  # a normal package
                ent = self.getPackageEntity(file_ent, ref_dict["ent"], ref_dict["ent_longname"])

            # Declare: kind id 192
            declare_ref = ReferenceModel.get_or_create(_kind=192, _file=file_ent, _line=ref_dict["line"],
                                                       _column=ref_dict["col"], _ent=ent, _scope=scope)

            # Declarein: kind id 193
            declarein_ref = ReferenceModel.get_or_create(_kind=193, _file=file_ent, _line=ref_dict["line"],
                                                         _column=ref_dict["col"], _scope=ent, _ent=scope)

    def addoverrideoverrideby(self, ref_dicts, file_ent, file_address , classesdict ):

        for ref_dict in ref_dicts:
            print('add Entity        ==)))))))))))))))))))))))))))))))))))))')
            scope = EntityModel.get_or_create(_kind=self.findKindWithKeywords(ref_dict["scope_kind"],
                                                                              ref_dict["scope_modifiers"]),
                                              _name=ref_dict["scope_name"],
                                              _parent=ref_dict["scope_parent"] if ref_dict[
                                                                                      "scope_parent"] is not None else file_ent,
                                              _longname=ref_dict["scope_longname"],
                                              _contents=ref_dict["scope_contents"])[0]



    def addCreateRefs(self, ref_dicts, file_ent, file_address):
        for ref_dict in ref_dicts:
            scope = EntityModel.get_or_create(_kind=self.findKindWithKeywords("Method", ref_dict["scopemodifiers"]),
                                              _name=ref_dict["scopename"],
                                              _type=ref_dict["scopereturntype"]
                                              , _parent=ref_dict["scope_parent"] if ref_dict[
                                                                                        "scope_parent"] is not None else file_ent
                                              , _longname=ref_dict["scopelongname"]
                                              , _contents=["scopecontent"])[0]
            # ent = self.getCreatedClassEntity(ref_dict["refent"], ref_dict["potential_refent"], file_address)
            # Create = ReferenceModel.get_or_create(_kind=190, _file=file_ent, _line=ref_dict["line"],
            #                                       _column=ref_dict["col"], _scope=scope, _ent=ent)
            # Createby = ReferenceModel.get_or_create(_kind=191, _file=file_ent, _line=ref_dict["line"],
            #                                         _column=ref_dict["col"], _scope=ent, _ent=scope)

    def getPackageEntity(self, file_ent, name, longname):
        # package kind id: 72
        ent = EntityModel.get_or_create(_kind=72, _name=name, _parent=file_ent,
                                        _longname=longname, _contents="")
        return ent[0]

    def getUnnamedPackageEntity(self, file_ent):
        # unnamed package kind id: 73
        ent = EntityModel.get_or_create(_kind=73, _name="(Unnamed_Package)", _parent=file_ent,
                                        _longname="(Unnamed_Package)", _contents="")
        return ent[0]

    def getClassProperties(self, class_longname, file_address):
        listener = ClassPropertiesListener()
        listener.class_longname = class_longname.split(".")
        listener.class_properties = None
        self.Walk(listener, self.tree)
        return listener.class_properties

    def getInterfaceProperties(self, interface_longname, file_address):
        listener = InterfacePropertiesListener()
        listener.interface_longname = interface_longname.split(".")
        listener.interface_properties = None
        self.Walk(listener, self.tree)
        return listener.interface_properties

    def getCreatedClassEntity(self, class_longname, class_potential_longname, file_address):
        props = p.getClassProperties(class_potential_longname, file_address)
        if not props:
            return self.getClassEntity(class_longname, file_address)
        else:
            return self.getClassEntity(class_potential_longname, file_address)

    def getClassEntity(self, class_longname, file_address):
        props = p.getClassProperties(class_longname, file_address)
        if not props:  # This class is unknown, unknown class id: 84
            ent = EntityModel.get_or_create(_kind=84, _name=class_longname.split(".")[-1],
                                            _longname=class_longname, _contents="")
        else:
            if len(props["modifiers"]) == 0:
                props["modifiers"].append("default")
            kind = self.findKindWithKeywords("Class", props["modifiers"])
            ent = EntityModel.get_or_create(_kind=kind, _name=props["name"],
                                            _longname=props["longname"],
                                            _parent=props["parent"] if props["parent"] is not None else file_ent,
                                            _contents=props["contents"])
        return ent[0]

    def getInterfaceEntity(self, interface_longname, file_address):  # can't be of unknown kind!
        props = p.getInterfaceProperties(interface_longname, file_address)
        if not props:
            return None
        else:
            kind = self.findKindWithKeywords("Interface", props["modifiers"])
            ent = EntityModel.get_or_create(_kind=kind, _name=props["name"],
                                            _longname=props["longname"],
                                            _parent=props["parent"] if props["parent"] is not None else file_ent,
                                            _contents=props["contents"])
        return ent[0]

    def getImplementEntity(self, longname, file_address):
        ent = self.getInterfaceEntity(longname, file_address)
        if not ent:
            ent = self.getClassEntity(longname, file_address)
        return ent


    def getoverrideEntity(self, longname, file_address):

        ent = self.getClassEntity(longname, file_address)

        return ent


    def findKindWithKeywords(self, type, modifiers):
        if len(modifiers) == 0:
            modifiers.append("default")
        leastspecific_kind_selected = None
        for kind in KindModel.select().where(KindModel._name.contains(type)):
            if self.checkModifiersInKind(modifiers, kind):
                if not leastspecific_kind_selected \
                        or len(leastspecific_kind_selected._name) > len(kind._name):
                    leastspecific_kind_selected = kind
        return leastspecific_kind_selected

    def checkModifiersInKind(self, modifiers, kind):
        for modifier in modifiers:
            if modifier.lower() not in kind._name.lower():
                return False
        return True

    def check(self, clsssmethods1 , classmethods2):
        for x in clsssmethods1:
            if x in classmethods2:
                return True

    def addoverridereference(self , classes , extendedfiles):
        for tuples in extendedfiles:
            main = tuples[0]
            fromx = tuples[1]

            methodsmain = classes[main]


            for x in  methodsmain:
                file = x['File']
                file_ent = self.getFileEntity(file)



                # print('Modifieeeeerrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr , '  ,x["scope_modifiers"])
                kindx = self.findKindWithKeywords(x["scope_kind"], x["scope_modifiers"])
                if kindx is None:
                    kindx = x['modifiersx']
                scope = EntityModel.get_or_create(_kind= kindx,_name=x["scope_name"],
                                                  _parent=x["scope_parent"] if x["scope_parent"] is not None else file_ent,
                                                  _longname=x["scope_longname"],
                                                  _contents=x["scope_contents"] , _type = x['Methodkind'])
                methodname1 = x['MethodIs']

                if (fromx in classes):
                    mathodsfrom = classes[fromx]
                    for y in mathodsfrom:

                        if y['MethodIs'] == methodname1:
                            print('--------------------------------------------------Reference override --------------------------------------------------------------------')
                            fe = self.getFileEntity(y['File'])
                            #
                            # print('Modifieeeeerrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrrr , ',
                            #       y["scope_modifiers"])
                            kind = self.findKindWithKeywords(y["scope_kind"],y["scope_modifiers"])
                            if kind is None:
                                kind = y['modifiersx']
                            ent = EntityModel.get_or_create(_kind= kind ,_name=y["scope_name"],
                                                      _parent=y["scope_parent"] if y["scope_parent"] is not None else  fe,
                                                      _longname=y["scope_longname"],
                                                      _contents=y["scope_contents"] ,_type = y['Methodkind']  )

                            print('ref.scope (entity performing reference)' , x['scope_longname']  , 'kind',  kindx )
                            print('ref.ent (entity being referenced)' ,  y['scope_longname']  , 'kind', kind )
                            print('File where the reference occurred' , x['File'] , 'line' , x['line'])
                            override_ref = ReferenceModel.get_or_create(_kind=211, _file=file_ent, _line=x["line"],_column= x["col"], _ent=ent[0], _scope=scope[0])
                            overrideBy_ref = ReferenceModel.get_or_create(_kind=212, _file= fe , _line=y["line"], _column=y["col"], _ent=scope[0] ,  _scope= ent[0])
                elif(x['is_overrided']):
                    overrideword = x[0]
                    if(overrideword not in classes):
                        ent = EntityModel.get_or_create(
                            _kind= 'Unknown Method',
                            _name=overrideword[1],
                            _parent= file_ent,
                            _longname= overrideword,
                            _contents= '', )
                        print('--------------------------------------------------Reference override -----------------------------------------------------------')
                        print('ref.scope (entity performing reference)', x['scope_longname'], 'kind',
                              self.findKindWithKeywords(x["scope_kind"], x["scope_modifiers"]))
                        print('ref.ent (entity being referenced)',overrideword, 'kind',self.findKindWithKeywords('Method', []))
                        print('File where the reference occurred', x['File'], 'line', x['line'])
                        override_ref = ReferenceModel.get_or_create(_kind=211, _file=file_ent, _line=x["line"],
                                                                    _column=x["col"], _ent=ent[0], _scope=scope[0])



###########
    def addcouplereference(self, classes , couples):
        keykind = ''
        for c in couples:
            file_ent = self.getFileEntity(c['File'])
            scope = EntityModel.get_or_create(_kind=self.findKindWithKeywords(c["scope_kind"],c["scope_modifiers"]), _name=c["scope_name"],
                                              _parent=c["scope_parent"] if c["scope_parent"] is not None else file_ent,
                                              _longname=c["scope_longname"],
                                              _contents=c["scope_contents"])
            if 'type_ent_longname' in c:
                keylist = c['type_ent_longname']
                if (len(keylist)!= 0):
                    for key in keylist:
                        if key in classes:
                            c1 = classes[key]
                            file_ent2 = self.getFileEntity(c1['File'])
                            keykind = self.findKindWithKeywords(c1["scope_kind"],c1["scope_modifiers"])
                            ent   = EntityModel.get_or_create(_kind=self.findKindWithKeywords(c1["scope_kind"],c1["scope_modifiers"]), _name=c1["scope_name"],
                                                          _parent=c1["scope_parent"] if c1["scope_parent"] is not None else file_ent2,
                                                          _longname=c1["scope_longname"],
                                                          _contents=c1["scope_contents"])
                            CoupleBy_ref = ReferenceModel.get_or_create(_kind=180, _file=file_ent2, _line=c["line"],
                                                                        _column=c["col"], _ent=scope[0], _scope=ent[0])

                        else :
                            kw = key.split('.')
                            keykind = "Unknown Class"
                            ent = EntityModel.get_or_create(_kind="Unknown Class", _name= kw[-1],
                                                          _parent= file_ent,
                                                          _longname=key,
                                                          )

                        print('Key' ,key)
                        Couple_ref = ReferenceModel.get_or_create(_kind=179, _file=file_ent, _line=c["line"],
                                                                _column=c["col"], _ent=ent[0], _scope=scope[0])
                        print('--------------------------------------------------Reference Couple -----------------------------------------')
                        print('ref.scope (entity performing reference)', c['scope_longname'], 'kind',
                              self.findKindWithKeywords(c["scope_kind"], c["scope_modifiers"]))
                        print('ref.ent (entity being referenced)', key, 'kind',
                             keykind)
                        print('File where the reference occurred', c['File'], 'line', c['line'])










#get_file #METHODS FROM db

if __name__ == '__main__':
    p = Project()
    create_db("../benchmark2_database.oudb",
              project_dir="..\benchmark")
    main()
    db = db_open("../benchmark2_database.oudb")

    # path = "D:/Term 7/Compiler/Final proj/github/OpenUnderstand/benchmark"
    path = "C:/Users/Asus/PycharmProjects/pythonProject1/benchmark/105_freemind"
    files = p.getListOfFiles(path)
    ########## AGE KHASTID YEK FILE RO RUN KONID:
    # files = ["../../Java codes/javaCoupling.java"]
    classesx= {}
    extendedlist= []
    classescoupleby = {}
    couple = []
    for file_address in files:
        try:
            file_ent = p.getFileEntity(file_address)
            tree = p.Parse(file_address)
            print('files' , file_address)
        except Exception as e:
            print("An Error occurred in file:" + file_address + "\n" + str(e))
            continue

        if (True):
            listener = overridelistener()
            listener.extendedtoentity = {}
            listener.set_dictionary(classesx)
            listener.set_file(file_address)
            listener.set_list(extendedlist)
            p.Walk(listener, tree)
            #print('parrrrrrrrrrrrttttttttttttttttttt',listener.get_classes)
            classesx = listener.get_classes
            extendedlist = listener.get_extendeds


        # except Exception as e:
        #     print('Error ' , e)
        #     print("An Error occurred for reference override in file:" + file_address + "\n" + str(e))
        if(True):
            # create
            # listener = CreateAndCreateBy()
            # listener.create = []
            # p.Walk(listener, tree)
            # p.addCreateRefs(listener.create, file_ent, file_address  )
            listener = CoupleAndCoupleBy()
            listener.set_file(filex=file_address)
            listener.set_classesx(classesx =classescoupleby)
            listener.set_couples( couples=couple)
            p.Walk(listener, tree)
            classescoupleby = listener.get_classes
            couple = listener.get_couples

        # except Exception as e:
        #     print("An Error occurred for reference couple in file:" + file_address + "\n" + str(e))
        # try:
        #     # declare
        #     listener = DeclareAndDeclareinListener()
        #     listener.declare = []
        #     p.Walk(listener, tree)
        #     p.addDeclareRefs(listener.declare, file_ent)
        # except Exception as e:
        #     print("An Error occurred for reference declare in file:" + file_address + "\n" + str(e))
        # try:
        #     # import
        #     listener = ImportListener()
        #     p.Walk(listener, tree)
        # except Exception as e:
        #     print("An Error occurred for reference import in file:" + file_address + "\n" + str(e))


    p.addoverridereference(classesx, extendedlist)
    p.addcouplereference(classescoupleby , couple)