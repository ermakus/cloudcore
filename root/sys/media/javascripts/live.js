	// Comet connection to cloudpub 
	// This required for Orbited
        var TCPSocket = Orbited.TCPSocket;

        // Plugin that handle connetion
        jQuery.fn.bunch = function(path) {

            	var server = "localhost";
            	var comet_port = 9999;
            	var client = new STOMPClient();
		var node = this;
		var id = p2id( path );

		var shutdown = false;		

		function status(message) {
			$('#status').html( message );
		}

		this.send = function( cmd ) {
			client.send( cmd, path );
			status( "SEND: " + cmd ); 
		}
	
		function connect() {
    			client.connect(server, comet_port, "foo", path);
		}
	
		status("Connecting to: " + path );

	    	client.onopen = function() {
			status("You connected to: " + path );
    			window.onbeforeunload = function() {
				shutdown = true;
        			client.unsubscribe( path );
    			};
    		};

    		client.onclose = function(c) {
			status("Connection lost, Code:" + c);
			if(!shutdown) if( confirm("Connection to server lost. Try to reconnect?") ) connect();
    		};

    		client.onerror = function(error) {
        		status("ERROR: " + error); 
    		};

    		client.onerrorframe = function(frame) {
        		status("ERROR FRAME:  " + frame.body); 
    		};

    		client.onconnectedframe = function() {
        		client.subscribe( path );
			node.send( "render " + path );
    		};

    		client.onmessageframe = function(frame) { //check frame.headers.destination?
			if( frame.body && frame.body[0] != '<' ) {
				// Plain text
				node.html("<pre>" + frame.body + "</pre>");
				return;
			}
			var msg = $(frame.body);
			var id = msg.attr('id');
			var me = $('#'+id);
			if( msg.is('delete') ) me.remove();
			else
			if( me.length ) me.replaceWith( msg );
			else 
			{
				var p = $( '#'+pid(id) );
				if( p.length ) 
					msg.appendTo( p );
				else
					node.html( msg );
			}
    		};

		connect();

		node.bind('click', function() {
		});

		node.html('<div id="' + id + '"/>');
		return node;
	}; 

	function p2id( path ) {
		return path.replace("/","_");
	}

	function id2p( path ) {
		return path.replace("_","/");
	}

	function pid( path ) {
		var idx = path.lastIndexOf("_");
		if( idx > 0 ) return path.substring( 0, idx );
                return "_";
	}

        $( function() {
		var root = $("#main_content_inner").bunch("/");
		$('#fu').bind('keypress', function(event) {
			if ((event.keyCode || event.which) == 13) { 
                              	var cmd = $(this).val();
				root.send( cmd );
				$(this).attr('value','');
				return false;
			}
		});
	});
 
