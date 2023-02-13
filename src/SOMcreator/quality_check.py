from . import constants, classes

def check_attribute_names(project:classes.Project):
    attribute_dict = {} #{lower_case:{attributeName:[attributes],attributename:[attributes]}}
    for obj in project.objects:
        for property_set in obj.property_sets:
            for attribute in property_set.attributes:
                name = attribute.name
                lower_case_name = name.lower()
                if lower_case_name not in attribute_dict:
                    attribute_dict[lower_case_name] = {}

                if name not in attribute_dict[lower_case_name]:
                       attribute_dict[lower_case_name][name] = list()

                attribute_dict[lower_case_name][name].append(attribute)

    problem_attributes = [name_dict for lower,name_dict in attribute_dict.items() if len(name_dict)>1]

    for d in problem_attributes:
        for name,attribute in d.items():
            print(name)
        print("----"*10)