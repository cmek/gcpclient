import google.auth
from google.cloud import compute_v1

import logging

logger = logging.getLogger(__name__)


class GCPClient:
    def __init__(self, project_id, region):
        self.region = region
        self.credentials, self.project = google.auth.default(
            scopes=["https://www.googleapis.com/auth/compute"]
        )
        self.project = project_id
        logger.debug(
            f"Initialized GCP with project: {self.project}, credentials: {self.credentials}"
        )

    def get_interconnects(self):
        client = compute_v1.InterconnectsClient(credentials=self.credentials)
        request = compute_v1.ListInterconnectsRequest(
            project=self.project,
        )
        response = client.list(request=request)
        logger.debug(f"Retrieved interconnects: {response}")
        return response

    def get_attachments(self):
        client = compute_v1.InterconnectAttachmentsClient(credentials=self.credentials)
        request = compute_v1.ListInterconnectAttachmentsRequest(
            project=self.project,
            region=self.region,
        )
        response = client.list(request=request)
        logger.debug(f"Retrieved interconnect attachments: {response}")
        return response

    def get_interconnect_attachment(self, attachment_id):
        client = compute_v1.InterconnectAttachmentsClient(credentials=self.credentials)
        request = compute_v1.GetInterconnectAttachmentRequest(
            interconnect_attachment=attachment_id,
            project=self.project,
            region=self.region,
        )
        response = client.get(request=request)
        logger.debug(f"Retrieved interconnect attachment: {response}")
        return response

    def get_interconnect_by_name(self, name):
        interconnects = self.get_interconnects()
        for interconnect in interconnects:
            if interconnect.name == name:
                logger.debug(f"Found interconnect by name: {interconnect}")
                return interconnect
        logger.debug(f"No interconnect found with name: {name}")
        return None

    def get_attachment_by_name(self, name):
        attachments = self.get_attachments()
        for attachment in attachments:
            if attachment.name == name:
                logger.debug(f"Found attachment by name: {attachment}")
                return attachment
        logger.debug(f"No attachment found with name: {name}")
        return None

    def delete_interconnect_attachment(self, attachment_id):
        client = compute_v1.InterconnectAttachmentsClient(credentials=self.credentials)
        request = compute_v1.DeleteInterconnectAttachmentRequest(
            interconnect_attachment=attachment_id,
            project=self.project,
            region=self.region,
        )
        operation = client.delete(request=request)
        logger.debug(f"Deleted interconnect attachment: {operation}")
        return operation

    def insert_interconnect_attachment(
        self, pairing_key, name, bandwidth, interconnect_name, vlan, metadata
    ):
        client = compute_v1.InterconnectAttachmentsClient(credentials=self.credentials)
        # this should be used in updating the metadata interconnect_name below
        az = pairing_key.split("/")[2]

        interconnect = self.get_interconnect_by_name(interconnect_name)
        if not interconnect:
            logger.error(f"Interconnect {interconnect_name} not found.")
            return None

        # expect the metadata to be a dict with the following keys:
        # interconnect_name (gcp-loc-sth-{az}
        # partner_name (name of the partner company)
        # portal_url (url to the partner portal)
        metadata = compute_v1.InterconnectAttachmentPartnerMetadata(**metadata)

        attachment = compute_v1.InterconnectAttachment(
            pairing_key=pairing_key,
            bandwidth=bandwidth,
            vlan_tag8021q=vlan,
            partner_metadata=metadata,
            name=name,
            interconnect=interconnect.self_link,
            type_="PARTNER_PROVIDER",
        )

        request = compute_v1.InsertInterconnectAttachmentRequest(
            project=self.project,
            region=self.region,
            interconnect_attachment_resource=attachment,
        )
        operation = client.insert(request=request)
        logger.debug(f"Inserted interconnect attachment: {operation}")
        return operation
