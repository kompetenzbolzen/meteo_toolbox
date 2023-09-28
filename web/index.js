// python3 -m http.server

const data_dir = 'data';
const index_file = "pmsl_t850.index.json";

var index = null;
var mapframe = null;

function httpGetAsync(url, callback)
{
    var xmlHttp = new XMLHttpRequest();
    xmlHttp.onreadystatechange = function() {
        if (xmlHttp.readyState == 4 && xmlHttp.status == 200)
            callback(xmlHttp.responseText);
    }
    xmlHttp.open("GET", url, true);
    xmlHttp.send(null);
}

function loadIndexFromJson(raw_text) {
	index = JSON.parse(raw_text);
	//TODO pass index here. that would be cleaner than public vars.
	build_interface();
}

function build_indexlist() {
	if (index==null) {
		return;
	}

	div = document.createElement('div');
	div.classList.add('index');

	list = document.createElement('ul');

	for (const i in index) {
		var map = index[i];

		a = document.createElement('a');
		a.classList.add('link');
		a.setAttribute('href', '');// data_dir + '/' + map.file);
		a.setAttribute('mapfile', map.file);
		a.onclick = indexlink_click;
		a.innerText = map.valid_offset;
		a.id = map.file;

		li = document.createElement('li');
		li.appendChild(a);
		list.appendChild(li);

	}

	div.appendChild(list);
	return div;
}

function indexlink_click(e) {
	console.log(this.id);

	mapframe.src = data_dir + '/' + this.getAttribute('mapfile');
	return false;
}

function build_mapframe() {
	div = document.createElement('div');
	div.classList.add('mapframe');
	frame = document.createElement('img');
	//frame.classList.add('mapframe');
	mapframe = frame;
	div.appendChild(frame);

	return div;
}

function build_interface() {
	index = build_indexlist();
	mapframe = build_mapframe();

	document.body.appendChild(index);
	document.body.appendChild(mapframe);
}

function clear_interface() {
	index.remove();
	mapframe.remove();
}

window.onload = function() {
	httpGetAsync(data_dir + '/' + index_file, loadIndexFromJson);
}
