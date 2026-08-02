<?php
header('Content-Type: application/json');
$payload = [
    'status' => 'ok',
    'application' => 'kiro-workshop-php',
    'marker' => 'PHP_OK_V1',
    'host' => gethostname(),
    'php' => PHP_VERSION,
    'os' => php_uname('s') . ' ' . php_uname('r'),
    'time' => gmdate('c')
];
echo json_encode($payload, JSON_UNESCAPED_SLASHES | JSON_PRETTY_PRINT);
?>
