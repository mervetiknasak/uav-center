from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [("api", "0022_move_flight_permits_to_forms")]

    operations = [migrations.DeleteModel(name="FlightPermit")]
