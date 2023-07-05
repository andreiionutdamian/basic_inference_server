

import os
from time import time

class _UploadMixin(object):
  """
  Mixin for upload functionalities that are attached to `libraries.logger.Logger`.

  This mixin cannot be instantiated because it is built just to provide some additional
  functionalities for `libraries.logger.Logger`

  In this mixin we can use any attribute/method of the Logger.
  """

  def __init__(self):
    super(_UploadMixin, self).__init__()
    return

  def minio_upload(self,
                   file_path, 
                   endpoint, 
                   access_key, 
                   secret_key, 
                   bucket_name, 
                   object_name=None,
                   days_retention=None,
                   debug=False,
                   return_object_name=False,
                   secure=False,
                   ):       
    """
    

    Parameters
    ----------
    file_path : str
      relative or full path to file.
    endpoint : str
      address of the MinIO server.
    access_key : str
      user.
    secret_key : str
      password.
    bucket_name : str
      preconfigureg bucket name.
    object_name : str, optional
      a object name - can be None and will be auto-generated. The default is None.
    days_retention : int, optional
      how many days before auto-delete. The default is None.
    debug : bool, optional
      The default is False.


    Returns
    -------
      Tuple(URL, Object_name) if return_object_name=True or just URL
      Returns URL of the downloadable file as well as the object name (or None in case o exception)
      Object_name can be further used with

    """            
    from minio import Minio
    from minio.commonconfig import GOVERNANCE
    from minio.retention import  Retention 
    from datetime import datetime as dttm
    from datetime import timedelta as tdelta
    from uuid import uuid4
    
    if object_name is None:
      object_name = "OBJ_"+ str(uuid4()).upper().replace('-','')
    
    try:
      start_up = time()
      client = Minio(
          endpoint=endpoint,
          access_key=access_key,
          secret_key=secret_key,
          secure=secure,
          )
      
      retention = None
      if days_retention is not None:
        date = dttm.utcnow().replace(
          hour=0, minute=0, second=0, microsecond=0,
          ) + tdelta(days=days_retention)
        retention = Retention(GOVERNANCE, date)

      self.P("Uploading '{} to minio ...".format(file_path))
      result = client.fput_object(
        file_path=file_path,
        bucket_name=bucket_name,
        object_name=object_name,
        retention=retention,
        )
      object_name = result.object_name
      url = client.presigned_get_object(
        bucket_name=result.bucket_name, 
        object_name=result.object_name,
        )
      self.P("Uploaded '{}' as '{}' in {:.2f}s".format(file_path, url, time()-start_up), color='g')
    except Exception as e:
      self.P(str(e), color='error')
      return None
    res = url
    if return_object_name:
      res = url, object_name

    return res

  def dropbox_upload(self,
                     access_token,
                     file_path,
                     target_path,
                     timeout=900,
                     chunk_size=4 * 1024 * 1024,
                     url_type='temporary',
                     progress_fn=None,
                     verbose=1,
                     ):

    """
    Uploads in the folder specific to a dropbox application.

    Steps:
      1. access https://www.dropbox.com/developers/apps
      2. create your app
      3. generate an unlimited access token

    Parameters
    ----------

    access_token : str
      The token generated in the dropbox app @ step 3

    file_path : str
      Path to the local file that needs to be uploaded in dropbox

    target_path : str
      Path to the remote dropbox path. Very important! This should start
      with '/' (e.g. '/DATA/file.txt')

    timeout : int, optional
      Parameter that is passed to the dropbox.Dropbox constructor
      The default is 900.

    chunk_size : int, optional
      Specifies how many bytes are uploaded progressively. If it's None,
      then the whole file is uploaded one time. Very important! If the
      file is big enough and `chunk_size=None` then errors may occur.
      The default is 4*1024*1024

    url_type : str
      Type of url to be generated after the file is uploaded: temporary or shared
    
    progress_fn: callback
      Will be used to report the current progress percent

    verbose: int, optional
      Verbosity level
      Default value 1
    
    Returns
    -------
      A downloadable link of the uploaded file

    """

    #TODO make it thread safe - remove tqdm and print only when the main thread calls the method

    def _progress(crt, total):
      return min(100.0, 100.0 * crt / total)
    
    assert url_type in ['temporary', 'shared']

    import dropbox
    
    uploaded_size = 0
    dbx = dropbox.Dropbox(access_token, timeout=timeout)

    if chunk_size is None:
      with open(file_path, 'rb') as f:
        dbx.files_upload(f.read(), target_path)
    else:
      with open(file_path, "rb") as f:
        file_size = os.path.getsize(file_path)
        if file_size <= chunk_size:
          dbx.files_upload(f.read(), target_path)
        else:
          upload_session_start_result = dbx.files_upload_session_start(
            f.read(chunk_size)
          )
          uploaded_size += chunk_size
          cursor = dropbox.files.UploadSessionCursor(
            session_id=upload_session_start_result.session_id,
            offset=f.tell(),
          )
          commit = dropbox.files.CommitInfo(path=target_path)
          while f.tell() < file_size:
            if (file_size - f.tell()) <= chunk_size:
              dbx.files_upload_session_finish(
                f.read(chunk_size), cursor, commit
              )
            else:
              dbx.files_upload_session_append(
                f.read(chunk_size),
                cursor.session_id,
                cursor.offset,
              )
              cursor.offset = f.tell()
            # endif
            # pbar.update(chunk_size)
            uploaded_size += chunk_size
            progress_prc = _progress(uploaded_size, file_size)
            if verbose >= 1 and self.is_main_thread:
              print('\r[...{}] Uploaded {:.2f}%'.format(file_path[-50:], progress_prc), flush=True, end='')

            if progress_fn:
              progress_fn(progress_prc)
          # end while
        # endif
      # endwith
    # endif

    url = None
    if url_type == 'temporary':
      url = dbx.files_get_temporary_link(target_path).link
    else:
      url = dbx.sharing_create_shared_link(target_path).url
    return url
  # enddef
