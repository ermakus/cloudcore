	// This required for Orbited
        var TCPSocket = Orbited.TCPSocket;

        // Plugin that handle connetion
        jQuery.fn.bunch = function(path, cmd) {

	        var node = this;
		var id = p2id( path );

            	var client = new TCPSocket();
	
		var shutdown = false;		

		function status(message) {
			$('#status').html( message );
		}

		this.send = function( cmd ) {
			client.send( cmd );
			status( "SEND: " + cmd ); 
		}
	
		status("Connecting to: " + path );

	    	client.onopen = function() {
			status("You connected to: " + path );
    			window.onbeforeunload = function() {
				shutdown = true;
        			client.close();
    			};
			if( cmd ) node.send( cmd ); else node.send( "render " + path );
  		};

    		client.onclose = function(c) {
			status("Connection lost, Code:" + c);
			if(!shutdown) if( confirm("Connection to server lost. Try to reconnect?") ) window.location.reload();
    		};

    		client.onread = function(body) { 
			if( body && body[0] != '<' ) {
				node.html("<pre>" + body + "</pre>");
				return;
			}
			var msg = $(body);
			if( msg.is('script') ) { /*$('#exec')*/ node.html( msg ); }
			else
			if( msg.is('delete') ) me.remove();
			else
			{
				var id = msg.attr('id');
				if( id ) var me = node.children('#'+id);
				if( me && me.length )
				{
					 me.replaceWith( msg );
				}
				else 
				{
					var p = me.children( '#'+pid(id) );
					if( p.length ) msg.appendTo( p ); else node.html( msg );
				}
			}
    		};

    		client.open("localhost", 9999, true);

		node.html('<div id="' + id + '"/>');
		return node;
	}; 

	function p2id( path ) {
		return path.replace(/\//g,"_");
	}

	function id2p( path ) {
		return path.replace(/_/g,"/");
	}

	function pid( path ) {
		var idx = path.lastIndexOf("_");
		if( idx > 0 ) return path.substring( 0, idx );
                return "_";
	}

        $( function() {
		var root = $("#main_content").bunch("/","render -l 1 -t root /");
		$("#sidebar_menu").load("/?template=menu&level=5", function() {
			$('body').delegate('.menu','click', function(event) {
				var path = id2p( $(this).attr("id") );
				root.send( "render -l 1 -t edit " + path );
				return true;
			});
		});
		$('#fu').bind('keypress', function(event) {
			if ((event.keyCode || event.which) == 13) { 
                              	var cmd = $(this).val();
				root.send( cmd );
				$(this).attr('value','');
				return false;
			}
		});
	});
 
