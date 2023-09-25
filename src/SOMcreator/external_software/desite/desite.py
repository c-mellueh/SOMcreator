from __future__ import annotations
import datetime
import xml.etree.ElementTree as ET
from xml.etree.ElementTree import Element
from lxml import etree

from src.SOMcreator import classes
output_date_time = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def handle_header(project: classes.Project, export_format: str) -> Element:
    ET.register_namespace("xsi", "http://www.w3.org/2001/XMLSchema-instance")
    xml_header = etree.Element(f'{{http://www.w3.org/2001/XMLSchema-instance}}{export_format}')
    xml_header.set("user", str(project.author))
    xml_header.set("date", str(output_date_time))
    xml_header.set("version", "3.0.1")  # TODO: Desite version hinzufügen
    return xml_header
