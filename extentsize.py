#!/usr/bin/python

# https://www.vmware.com/support/developer/vddk/vmdk_50_technote.pdf

import sys
import os.path


EXTENT_ACCESS = [ "RW", "RDONLY", "NOACCESS" ]
EXTENT_TYPE = [ "FLAT", "SPARSE", "ZERO", "VMFS", "VMFSSPARSE", "VMFSRDM", "VMFSRAW" ]


"""
Main process function.

- Open file
- Read lines
- Pass the lines and sizes to the process_lines function
- Reset file pointer
- Clear current file content
- Write new content
- Close file
"""
def process( file, sizes ):
	sizes_list = split_sizes( sizes )
	if( file_exists( file ) and valid_sizes( sizes_list ) ):
		print( "Opening file: " + file )
		f = open( file, "r+" )
		lines = f.readlines()
		lines = process_lines( sizes_list, lines )
		f.seek( 0 )
		f.truncate( 0 )
		print( "Write content to file." )
		f.writelines( lines )
		f.close()
		print( "Done!" )


"""
Process all lines of the file.

Per line:
- Determine if the line is an extent (by finding access and type)
- If the sizes list is not exhausted,
  and the size is not an asterisk, set the size

Return the new content, with size(s) replaced.
"""
def process_lines( sizes_list, lines ):
	size_index = 0
	for i in range( len( lines ) ):
		if( size_index < len( sizes_list ) ):
			line  = lines[i]
			line = prepare_line( line )
			access_end = -1
			type_begin = -1

			for access in EXTENT_ACCESS :
				if( access in line ):
					access_end = line.index( access ) + len( access )
			for type in EXTENT_TYPE:
				if( type in line ):
					type_begin = line.index( type )

			if( ( access_end >=0 ) and ( type_begin >= 0 ) and ( access_end < type_begin ) ):
				print( "Extent line found:" )
				print( lines[i] )
				size = sizes_list[size_index]

				if( size != "*" ):
					print( "Set extent size to: " + size )
					orig_line = lines[i]
					replaced = process_line( line, orig_line, access_end, type_begin, size )
					lines[i] = replaced
				else:
					print( "Ignoring extent (size *)" )

				size_index += 1
	return lines


"""
Replaces the size in the extent line.
"""
def process_line( line, orig_line, access_end, type_begin, size ):
	line_index = access_end
	chars = list( line )
	size_begin = -1
	size_end = -1

	while( line_index < type_begin ):
		char = chars[line_index]
		if( size_begin == -1 ):
			if( char.isdigit() ):
				size_begin = line_index
		if( ( size_begin != -1 ) and ( char.isdigit() ) ):
			size_end = line_index
		line_index += 1

	replaced = orig_line[:size_begin]
	replaced += size
	replaced += orig_line[size_end + 1:]

	return replaced


"""
Prepares the line for processing.

- Uppercase the given line
- Strip everything after the first double quote
  (if we are in an extent this is the filename and everything after that)
- Remove comments (everything after #)
"""
def prepare_line( line ):
	line = line.upper()

	if( "\"" in line ):
		string_start = line.index( "\"" )
		line = line[:string_start]

	if( "#" in line ):
		comment_start = line.index( "#" )
		line = line[:comment_start]
	return line


"""
Split the sizes (on comma) and then trim spaces.
"""
def split_sizes( sizes ):
	if( sizes ):
		sizes_list = sizes.split( "," )
		i = 0
		for i in range( len(sizes_list ) ):
			sizes_list[i] = sizes_list[i].strip()

		return sizes_list
	else:
		return False


def file_exists( file ):
	if( not os.path.isfile( file ) ):
		print( "" )
		print( "File does not exits: " + file )
		return False
	else:
		return True


"""
Checks whether the given size (collection) is valid.
"""
def valid_sizes( sizes_list ):
	if( not sizes_list ):
		error( "No size found" )
		return False

	for size in sizes_list:
		if( size != "*" and not size.isdigit() ):
			print( "Invalid size: " + size )
			return False

	return True


"""
Prints usage instructions and examples.
"""
def print_usage():
	print( "" )
	print( "    Usage examples:" )
	print( "        script.py -f:file.vmdk -s:4192256" )
	print( "        script.py -s:*,*,20971520 -f:file.vmdk" )
	print( "        script.py -f:\"/path with spaces/file.vmdk\" -s:1048576" )
	print( "" )
	print( "    Arguments:" )
	print( "        -f: Path of the VMDK file." )
	print( "        -s: New size in sectors." )
	print( "            Separate sizes with commas for multiple extents." )
	print( "            Use an asterisk to leave the size as is." )
	print( "            The number of sizes does not need to be equal to the number of extents." )
	print( "        -h  Shows help text." )
	print( "" )


"""
Prints the help text.
"""
def print_help():
	print( "" )
	print( "This script can be used to change the size" )
	print( "of extents (numer of sectors) in a VMDK file." )
	print_usage()


"""
Helper function to print error (and usage).
"""
def error( message ):
	print( "" )
	print( message )
	print_usage()


"""
Handles calls, where one argument is given.
Basically show error or call print_help().
"""
def one_argument( arg ):
	if( arg.strip() == "-h" ):
		print_help()
	elif( arg.startswith( "-f:" ) ):
		error( "Size argument (-s:) not found." )
	elif( arg.startswith( "-s:" ) ):
		error( "File argument (-f:) not found." )
	else:
		error( "Invalid (or incomplete) argument found: " + arg )


"""
Handles calls where two args are given.
If the args are valid, calls the main process function.
"""
def two_arguments( arg1, arg2 ):
	if( arg1.startswith( "-f:" ) and arg2.startswith( "-s:" ) ):
		file = arg1[3:]
		sizes = arg2[3:]
		process(file, sizes)
	elif( arg1.startswith( "-s:" ) and arg2.startswith( "-f:" ) ):
		sizes = arg1[3:]
		file = arg2[3:]
		process( file, sizes )
	else:
		error( "Invalid (or incomplete) arguments found." )


"""
Entry point.
Does some very basic args checking.
Passes on control if the number of args is valid.
"""
def main( args ):
	arg_count = len( args )

	if( arg_count == 1 ):
		error( "No arguments found." )
	elif( arg_count == 2 ):
		one_argument( args[1] )
	elif( arg_count == 3 ):
		two_arguments( args[1], args[2] )
	else:
		error( "Too many arguments found." )


# Call the main function and pass the arguments.
main( sys.argv )
