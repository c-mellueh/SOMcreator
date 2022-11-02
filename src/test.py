import SOMcreator.classes as classes
proj = classes.Project("test")
path = "C:/Users/ChristophMellueh/Desktop/excel_test.xlsx"
proj.import_excel(path)
for obj in classes.Object:
    print(obj.parent)
