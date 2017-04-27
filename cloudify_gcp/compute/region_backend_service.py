from cloudify import ctx
from cloudify.decorators import operation

from .. import utils

from cloudify_gcp.gcp import check_response
from cloudify_gcp.compute.backend_service import BackendService


class RegionBackendService(BackendService):
    def __init__(self,
                 config,
                 logger,
                 name,
                 region,
                 health_check=None,
                 additional_settings=None,
                 backends=None):
        """
        Create RegionBackendService

        :param config:
        :param logger:
        :param region: region name where backend in emplaced:
        :param health_check:
        :param backends:
        :param additional_settings:
        """
        super(RegionBackendService, self).__init__(
            config, logger, name,
            health_check=health_check,
            additional_settings=additional_settings,
            backends=backends)

        self.region = region

    def to_dict(self):
        body = super(BackendService, self)
        body['region'] = self.region
        gcp_settings = {utils.camel_farm(key): value
                        for key, value in self.additional_settings.iteritems()}
        body.update(gcp_settings)
        return body

    @check_response
    def get(self):
        return self.discovery.regionBackendServices().get(
            project=self.project,
            backendService=self.name).execute()

    @check_response
    def list(self):
        return self.discovery.regionBackendServices().list(
            project=self.project).execute()

    @utils.async_operation(get=True)
    @check_response
    def create(self):
        return self.discovery.regionBackendServices().insert(
            project=self.project,
            body=self.to_dict()).execute()

    @utils.async_operation()
    @check_response
    def delete(self):
        return self.discovery.regionBackendServices().delete(
            project=self.project,
            backendService=self.name).execute()

    @check_response
    def set_backends(self, backends):
        body = {
            'backends': backends
        }
        self.backends = backends
        return self.discovery.regionBackendServices().patch(
            project=self.project,
            backendService=self.name,
            body=body).execute()

    @utils.sync_operation
    def add_backend(self, current_backends, group_self_url):
        new_backend = {'group': group_self_url}
        backends = current_backends + [new_backend]
        return self.set_backends(backends)

    @utils.sync_operation
    def remove_backend(self, current_backends, group_self_url):
        backends = filter(lambda backend: backend['group'] != group_self_url,
                          current_backends)
        return self.set_backends(backends)


@operation
@utils.throw_cloudify_exceptions
def create(name, region, health_check, additional_settings, **kwargs):
    name = utils.get_final_resource_name(name)
    gcp_config = utils.get_gcp_config()
    regional_backend_service = RegionBackendService(gcp_config,
                                                    ctx.logger,
                                                    name,
                                                    region,
                                                    health_check,
                                                    additional_settings)

    utils.create(regional_backend_service)


@operation
@utils.retry_on_failure('Retrying deleting backend service')
@utils.throw_cloudify_exceptions
def delete(**kwargs):
    gcp_config = utils.get_gcp_config()
    name = ctx.instance.runtime_properties.get('name')

    regional_backend_service = RegionBackendService(gcp_config,
                                                    ctx.logger,
                                                    name=name)
    utils.delete_if_not_external(regional_backend_service)
