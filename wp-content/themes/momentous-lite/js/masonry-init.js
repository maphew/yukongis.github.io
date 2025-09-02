/*! Momentous masonry.js
  Adds support for Masonry Layout
  Author: Thomas W (themezee.com)
*/
jQuery(document).ready(function($) {

	// Set Masonry Container
	var $container = $('#post-wrapper');

	// initialize Masonry after all images have loaded  
	$container.imagesLoaded( function() {
		$container.masonry({
			itemSelector: '.post-wrap'
		});
	});

});