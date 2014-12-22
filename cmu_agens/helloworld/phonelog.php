<?
### phonelog.php
	header('Content-type: application/vnd.google-earth.kml+xml');
	header('Content-disposition: attachment;filename="hello_world.kml"');
	echo '<?xml version="1.0" encoding="UTF-8"?>' . "\n";
	echo '<kml xmlns="http://earth.google.com/kml/2.0">' ."\n";
	echo '<Document>' . "\n";
	$phonelog = file("phonelog.txt");
	foreach ($phonelog as $entry) {
	$fields = explode("\t", trim($entry));
	if ($fields[4] == "None" || $fields[5] == "None") continue;
	?>
	<Placemark>
		<Snippet><?= htmlspecialchars($fields[3]) ?></Snippet>
		<name><?= htmlspecialchars($fields[1]) ?></name>
		<LookAt>
			<longitude><?= $fields[5] ?></longitude>
			<latitude><?= $fields[4] ?></latitude>
			<range>1000000</range>
		</LookAt>
		<visibility>1</visibility>
		<Point>
			<extrude>1</extrude>
			<altitudeMode>relativeToGround</altitudeMode>
			<coordinates>
				<?= $fields[5] . "," . $fields[4] ?>,0
			</coordinates>
		</Point>
	</Placemark>
	<? }
?>
</Document>
</kml>
