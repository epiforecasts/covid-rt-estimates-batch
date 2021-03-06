from definitions.date_standards import EVEN_DAYS
from definitions.processable_entities import Dataset, Derivative

SCHEDULE = [Dataset("united-kingdom",
                    data_dir="subnational/united-kingdom/cases"),
            Dataset("united-kingdom-deaths",
                    data_dir="subnational/united-kingdom/deaths"),
            Dataset("united-kingdom-admissions",
                    data_dir="subnational/united-kingdom/admissions"),
            Dataset("united-kingdom-local",
                    data_dir="subnational/united-kingdom-local/cases",
                    max_wall_clock_minutes=24*60),
            Dataset("united-kingdom-local-deaths",
                    data_dir="subnational/united-kingdom-local/deaths",
                    max_wall_clock_minutes=24*60),
            Dataset("united-kingdom-local-admissions",
                    data_dir="subnational/united-kingdom-local/admissions",
                    max_wall_clock_minutes=24*60),
            Dataset("united-states",
                    data_dir="subnational/united-states/cases"),
            Dataset("regional-cases", data_dir="region/cases"),
            Dataset("regional-deaths", data_dir="region/deaths"),
            Dataset("cases", data_dir="national/cases"),
            Dataset("deaths", data_dir="national/deaths"),
            Dataset("belgium", data_dir="subnational/belgium/cases"),
            Dataset("brazil", data_dir="subnational/brazil/cases"),
            Dataset("canada", data_dir="subnational/canada/cases"),
            Dataset("colombia", data_dir="subnational/colombia/cases"),
            Dataset("germany", data_dir="subnational/germany/cases"),
            Dataset("india", data_dir="subnational/india/cases"),
            Dataset("italy", data_dir="subnational/italy/cases"),
            Derivative("united-kingdom-collated",
                       data_dir="subnational/united-kingdom/collated",
                       dependencies=["united-kingdom",
                                     "united-kingdom-deaths",
                                     "united-kingdom-admissions"])
            ]
