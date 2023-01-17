id = desiteThis.ID();
pset = "Allgemeine_Eigenschaften:";
ident_attrib = "bauteilKlassifikation";

stat = desiteAPI.getPropertyValue(id, "Check_State", "xs:string");
objekttyp = desiteAPI.getPropertyValue(id, pset + ident_attrib, "xs:string");

if (stat == "Ungeprüft") {
    desiteResult.setCheckState('failed');

    check_status = "Failed"
    desiteAPI.setPropertyValue(id, "Check_State", "xs:string", check_status);

}

if (objekttyp == undefined) {
    desiteResult.addMessage(pset + "Objekttyp existiert nicht -> Prüfung kann nicht durchgeführt Werden [Fehler 8]");
    desiteAPI.setPropertyValue(id, "Check_State", "xs:string", "Failed");
    desiteResult.setCheckState("Failed")

} else {
    desiteResult.addMessage(pset + ident_attrib + " (" + objekttyp + ") konnte nicht in SOM gefunden werden [Fehler 7]")
}

desiteAPI.setPropertyValue(id, "zu_pruefende_eigenschaften", "xs:int", 1);
desiteAPI.setPropertyValue(id, "fehlerhafte_eigenschaften", "xs:int", 1);