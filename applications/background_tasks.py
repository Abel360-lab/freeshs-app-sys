"""
Simple background task processor using threading.
"""

import threading
import time
import logging
from queue import Queue, Empty
from django.conf import settings

logger = logging.getLogger(__name__)


class BackgroundTaskProcessor:
    """Simple background task processor using threading."""
    
    def __init__(self):
        self.task_queue = Queue()
        self.worker_thread = None
        self.running = False
        self.start_worker()
    
    def start_worker(self):
        """Start the background worker thread."""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._worker_loop, daemon=True)
            self.worker_thread.start()
            logger.info("Background task processor started")
    
    def stop_worker(self):
        """Stop the background worker thread."""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        logger.info("Background task processor stopped")
    
    def _worker_loop(self):
        """Main worker loop that processes tasks."""
        while self.running:
            try:
                # Get task from queue with timeout
                task = self.task_queue.get(timeout=1)
                
                if task is None:  # Shutdown signal
                    break
                
                # Process the task
                self._process_task(task)
                
            except Empty:
                # No tasks in queue, continue
                continue
            except Exception as e:
                logger.error(f"Error in background worker: {str(e)}")
                time.sleep(1)
    
    def _process_task(self, task):
        """Process a single task."""
        try:
            task_func = task.get('function')
            args = task.get('args', [])
            kwargs = task.get('kwargs', {})
            
            logger.info(f"Processing background task: {task_func.__name__}")
            
            # Execute the task
            result = task_func(*args, **kwargs)
            
            logger.info(f"Background task completed: {task_func.__name__}")
            
            # Call success callback if provided
            success_callback = task.get('success_callback')
            if success_callback:
                success_callback(result)
                
        except Exception as e:
            logger.error(f"Error processing background task: {str(e)}")
            
            # Call error callback if provided
            error_callback = task.get('error_callback')
            if error_callback:
                error_callback(e)
    
    def enqueue_task(self, task_func, *args, success_callback=None, error_callback=None, **kwargs):
        """Enqueue a task for background processing."""
        task = {
            'function': task_func,
            'args': args,
            'kwargs': kwargs,
            'success_callback': success_callback,
            'error_callback': error_callback
        }
        
        self.task_queue.put(task)
        logger.info(f"Task enqueued: {task_func.__name__}")


# Global task processor instance
task_processor = BackgroundTaskProcessor()


def enqueue_pdf_generation(application_id):
    """Enqueue PDF generation task for an application."""
    from .tasks import generate_application_pdf_task
    
    def on_success(result):
        logger.info(f"PDF generation successful for application {application_id}")
    
    def on_error(error):
        logger.error(f"PDF generation failed for application {application_id}: {str(error)}")
    
    task_processor.enqueue_task(
        generate_application_pdf_task,
        application_id,
        success_callback=on_success,
        error_callback=on_error
    )


def enqueue_application_processing(application_id):
    """Enqueue complete application processing (PDF + email)."""
    from .tasks import process_application_submission
    
    def on_success(result):
        logger.info(f"Application processing successful for {application_id}")
    
    def on_error(error):
        logger.error(f"Application processing failed for {application_id}: {str(error)}")
    
    task_processor.enqueue_task(
        process_application_submission,
        application_id,
        success_callback=on_success,
        error_callback=on_error
    )


# Cleanup function for Django app shutdown
def cleanup_background_tasks():
    """Cleanup background tasks on app shutdown."""
    task_processor.stop_worker()
