<?
### phonehome.php

	if (isset($_GET['reset'])) {
		$phonelog = fopen("phonelog.txt", "w");
		fclose($phonelog);
		echo "Cleared Phone Log.";
		die();
	}
	if (!isset($_POST['site_id'])) die;
	$existinglog = file("phonelog.txt");
	foreach ($existinglog as $entry) {
		$f = explode("\t", trim($entry));
		if ($f[0] == $_POST['site_id']) die;
	}

	$phonelog = fopen("phonelog.txt", "a");
	fwrite($phonelog, $_POST['site_id'] . "\t" . $_POST['name'] .
		"\t" . $_POST['login_base'] . "\t" . $_POST['url'] .
		"\t" . $_POST['latitude'] . "\t" . $_POST['longitude'] .
		"\n");
	fclose($phonelog);
?>
