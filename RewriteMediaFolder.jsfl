var doc = fl.getDocumentDOM();
if (!doc) {
    alert("No document open.");
} else {
    var lib = doc.library;
    var xflPath = doc.pathURI;
    var projectFolder = xflPath.substring(0, xflPath.lastIndexOf("/"));
    var mediaFolder = projectFolder + "/library/updated_media";

    var mediaFolderPath = FLfile.uriToPlatformPath(mediaFolder);
    var exported = 0;

    // Delete existing contents of the media folder
    if (FLfile.exists(mediaFolder)) {
        var files = FLfile.listFolder(mediaFolder + "/*", "files");
        for (var j = 0; j < files.length; j++) {
            FLfile.remove(mediaFolder + "/" + files[j]);
        }
    } else {
        FLfile.createFolder(mediaFolder);
    }

    // Export all bitmaps in the library
    for (var i = 0; i < lib.items.length; i++) {
        var item = lib.items[i];
        if (item.itemType === "bitmap") {
            var outputPath = mediaFolder + "/" + item.name + ".png";
            item.exportToFile(outputPath);
            fl.trace("Exported: " + item.name);
            exported++;
        }
    }

    alert("Rewritten media folder with " + exported + " bitmap(s).");
}
